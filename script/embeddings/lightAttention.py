#!/usr/bin/env python3

import argparse
import logging
import shutil
import sys
from pathlib import Path

import h5py
import requests
import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset
from tqdm import tqdm


def main():
    args = parse_arguments()

    # Set up logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Determine device
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    logger.info(f'Using device: {device}')

    # Ensure the input file exists
    if not args.input_h5.is_file():
        logger.error(f"Input file {args.input_h5} does not exist.")
        sys.exit(1)

    # Handle the model checkpoint
    checkpoint_path = handle_checkpoint(args.checkpoint, logger)

    # Load the model
    model = load_model(checkpoint_path, device, logger)

    # Check if processing is necessary
    keys_to_process = get_keys_to_process(args.input_h5, args.output)
    if not keys_to_process:
        logger.info("All embeddings have already been processed.")
        sys.exit(0)
    else:
        logger.info(f"{len(keys_to_process)} embeddings to process.")

    # Create Dataset and DataLoader
    dataset = H5Dataset(args.input_h5, keys_to_process)
    data_loader = DataLoader(
        dataset,
        batch_size=args.batch_size,
        collate_fn=collate_fn,
        num_workers=0  # Adjust if multiprocessing is needed
    )

    # Process data in batches and save outputs
    with H5Saver(args.output) as h5_saver:
        for batch_embs, batch_masks, header_list in tqdm(data_loader, desc='Processing batches', unit='batch'):
            batch_embs = batch_embs.to(device).float()
            batch_masks = batch_masks.to(device)
            representations = process_batch(model, batch_embs, batch_masks)
            representations = representations.cpu().numpy()  # Move to CPU for saving
            # Save each representation to the output H5 file
            h5_saver.save_batch(header_list, representations)

    logger.info(f'Processing complete. Representations saved to {args.output}')


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description='Process ProtT5 residue embeddings using LightAttention model.')
    parser.add_argument(
        'input_h5',
        type=Path,
        help='Path to the input H5 file containing ProtT5 residue embeddings.'
    )
    parser.add_argument(
        '--checkpoint',
        type=Path,
        default=None,
        help='Optional path to the model checkpoint. If not provided, it will be downloaded.'
    )
    parser.add_argument(
        '--batch_size',
        type=int,
        default=32,
        help='Batch size for processing (default: 32).'
    )
    parser.add_argument(
        '--output',
        type=Path,
        default=Path('la_representation.h5'),
        help='Output H5 file to save the representations (default: la_representation.h5).'
    )
    return parser.parse_args()


def handle_checkpoint(checkpoint_arg, logger):
    """Handle model checkpoint loading or downloading."""
    if checkpoint_arg and checkpoint_arg.is_file():
        checkpoint_path = checkpoint_arg
        logger.info(f'Loading model checkpoint from {checkpoint_path}')
    else:
        # Download the model checkpoint
        weights_link = 'http://data.bioembeddings.com/public/embeddings/feature_models/light_attention/la_prott5_subcellular_localization.pt'
        checkpoint_path = Path('la_prott5_subcellular_localization.pt')
        if not checkpoint_path.is_file():
            logger.info('Model checkpoint not provided or does not exist. Downloading...')
            download_file(weights_link, checkpoint_path)
        else:
            logger.info(f'Using existing model checkpoint at {checkpoint_path}')
    return checkpoint_path


def download_file(url: str, destination: Path):
    """Download a file from a URL to a local destination."""
    response = requests.get(url, stream=True)
    if response.status_code != 200:
        raise Exception(f"Failed to download file from {url}. Status code: {response.status_code}")
    total_size = int(response.headers.get('content-length', 0))
    with open(destination, 'wb') as file, tqdm(
        desc=f'Downloading {destination.name}',
        total=total_size,
        unit='iB',
        unit_scale=True,
        unit_divisor=1024,
    ) as bar:
        for data in response.iter_content(chunk_size=1024):
            size = file.write(data)
            bar.update(size)


def load_model(checkpoint_path: Path, device: str, logger):
    """Load the LightAttention model from checkpoint."""
    model = LightAttention(output_dim=10)
    state = torch.load(checkpoint_path, map_location=device)
    # Adjust loading based on the checkpoint's structure
    if "model_state_dict" in state:
        model.load_state_dict(state["model_state_dict"])
    else:
        model.load_state_dict(state)
    model = model.eval().to(device)
    logger.info("Model loaded successfully.")
    return model


def get_keys_to_process(input_h5_path: Path, output_h5_path: Path):
    """Return a list of keys that need to be processed."""
    with h5py.File(input_h5_path, 'r') as hdf_in:
        input_keys = set(hdf_in.keys())

    if output_h5_path.is_file():
        with h5py.File(output_h5_path, 'r') as hdf_out:
            output_keys = set(hdf_out.keys())
    else:
        output_keys = set()

    remaining_keys = list(input_keys - output_keys)
    return remaining_keys


def process_batch(model: nn.Module, batch_embs: torch.Tensor, batch_masks: torch.Tensor) -> torch.Tensor:
    """Process a batch of embeddings through the model."""
    with torch.no_grad():
        representations = model(batch_embs, batch_masks)
    return representations


class LightAttention(nn.Module):
    """LightAttention model for subcellular localization prediction."""

    def __init__(
        self,
        embeddings_dim: int = 1024,
        output_dim: int = 11,
        dropout: float = 0.25,
        kernel_size: int = 9,
        conv_dropout: float = 0.25,
    ):
        super().__init__()

        self.feature_convolution = nn.Conv1d(
            embeddings_dim, embeddings_dim, kernel_size, stride=1, padding=kernel_size // 2
        )
        self.attention_convolution = nn.Conv1d(
            embeddings_dim, embeddings_dim, kernel_size, stride=1, padding=kernel_size // 2
        )

        self.softmax = nn.Softmax(dim=-1)
        self.dropout = nn.Dropout(conv_dropout)
        self.linear = nn.Sequential(
            nn.Linear(2 * embeddings_dim, 32),
            nn.Dropout(dropout),
            nn.ReLU(),
            nn.BatchNorm1d(32),
        )
        self.output = nn.Linear(32, output_dim)
        self.id0 = nn.Identity()

    def forward(self, x: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: [batch_size, embeddings_dim, sequence_length] embedding tensor to classify
            mask: [batch_size, sequence_length] mask corresponding to zero padding. Padding positions are False.

        Returns:
            extraction: [batch_size, embeddings_dim] tensor with extracted features
        """
        attention = self.attention_convolution(x)  # [batch_size, embeddings_dim, sequence_length]

        # Mask out padding
        attention = attention.masked_fill(~mask[:, None, :], -1e9)

        # Extract features using attention mechanism
        extraction = torch.sum(x * self.softmax(attention), dim=-1)
        extraction = self.id0(extraction)

        # --- Actual inference (commented out as per your original script) ---
        # o = self.feature_convolution(x)
        # o = self.dropout(o)
        # o1 = torch.sum(o * self.softmax(attention), dim=-1)
        # o1 = self.id1(o1)
        # o2, _ = torch.max(o, dim=-1)
        # o = torch.cat([o1, o2], dim=-1)
        # o = self.id2(o)
        # o = self.linear(o)
        # return self.output(o)

        return extraction  # [batch_size, embeddings_dim]


class H5Dataset(Dataset):
    """Dataset for reading embeddings from an H5 file."""

    def __init__(self, h5_file_path: Path, keys_to_process: list):
        self.h5_file_path = h5_file_path
        self.keys = keys_to_process
        self.hdf_in = None  # Will be initialized in __getitem__

    def __len__(self):
        return len(self.keys)

    def __getitem__(self, idx):
        if self.hdf_in is None:
            # Each worker should have its own file handle
            self.hdf_in = h5py.File(self.h5_file_path, 'r')
        key = self.keys[idx]
        emb = self.hdf_in[key][()]
        residue_emb = torch.tensor(emb)
        mask = torch.ones(residue_emb.shape[0], dtype=torch.bool)
        residue_emb = residue_emb.permute(1, 0)  # From [L, C] to [C, L]
        return residue_emb, mask, key

    def __del__(self):
        if self.hdf_in is not None:
            self.hdf_in.close()


def collate_fn(batch):
    """Collate function for DataLoader to pad sequences and create masks."""
    emb_list, mask_list, key_list = zip(*batch)
    max_len = max(emb.shape[1] for emb in emb_list)
    batch_size = len(emb_list)
    emb_dim = emb_list[0].shape[0]

    # Initialize tensors for batch embeddings and masks
    batch_embs = torch.zeros(batch_size, emb_dim, max_len)
    batch_masks = torch.zeros(batch_size, max_len, dtype=torch.bool)

    # Copy data into tensors
    for i, (emb, mask) in enumerate(zip(emb_list, mask_list)):
        seq_len = emb.shape[1]
        batch_embs[i, :, :seq_len] = emb
        batch_masks[i, :seq_len] = mask

    return batch_embs, batch_masks, key_list


class H5Saver:
    """Context manager for saving embeddings to an H5 file."""

    def __init__(self, output_path: Path):
        self.output_path = output_path
        self.temp_path = output_path.with_suffix('.temp.h5')
        self.h5_out = None

    def __enter__(self):
        # Open the output H5 file in append mode
        self.h5_out = h5py.File(self.temp_path, 'a', libver='latest')
        return self

    def save_batch(self, header_list, embeddings):
        """Save a batch of embeddings to the H5 file."""
        for header, embedding in zip(header_list, embeddings):
            self.h5_out.create_dataset(header, data=embedding)

        # Flush to ensure data is written to disk
        self.h5_out.flush()

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.h5_out is not None:
            self.h5_out.close()
        # Safely move the temp file to the final destination
        try:
            if exc_type is None:
                # No exception, replace the original file
                self._replace_file()
            else:
                print("An error occurred during processing. The original output file remains unchanged.")
        finally:
            # Clean up temp file if it still exists
            if self.temp_path.exists():
                self.temp_path.unlink()

    def _replace_file(self):
        if self.output_path.exists():
            backup_path = self.output_path.with_suffix('.backup.h5')
            shutil.move(self.output_path, backup_path)
            shutil.move(self.temp_path, self.output_path)
            backup_path.unlink()  # Remove the backup
        else:
            shutil.move(self.temp_path, self.output_path)


if __name__ == '__main__':
    main()
