#!/usr/bin/env python3

import argparse
from pathlib import Path
import sys
import torch
import h5py
import numpy as np
from torch.utils.data import Dataset, DataLoader
from torch import nn
import requests
from tqdm import tqdm

def main():
    args = parse_arguments()
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f'Using device: {device}')

    ensure_input_file_exists(args.input_h5)
    keys_to_process = check_needed_process(args.input_h5, args.output)
    checkpoint_path = handle_checkpoint(args.checkpoint)
    model = load_model(checkpoint_path, device)

    dataset = H5Dataset(args.input_h5, keys_to_process)
    data_loader = DataLoader(
        dataset,
        batch_size=args.batch_size,
        collate_fn=collate_fn,
        num_workers=0  # Set >0 for multiprocessing, handle with care
    )

    process_data(model, data_loader, args.output, device)

def parse_arguments():
    parser = argparse.ArgumentParser(description='Process ProtT5 residue embeddings using LightAttention model.')
    parser.add_argument('input_h5', type=Path, help='Path to the input H5 file containing ProtT5 residue embeddings.')
    parser.add_argument('--checkpoint', type=Path, help='Optional path to the model checkpoint. If not provided, it will be downloaded.')
    parser.add_argument('--batch_size', type=int, default=32, help='Batch size for processing (default: 32).')
    parser.add_argument('--output', type=Path, default=Path('la_representation.h5'), help='Output H5 file to save the representations (default: la_representation.h5).')
    return parser.parse_args()

def ensure_input_file_exists(input_path):
    if not input_path.is_file():
        print(f"Error: Input file {input_path} does not exist.", file=sys.stderr)
        sys.exit(1)

def check_needed_process(input_h5_path: Path, output_h5_path: Path):
    def get_keys_to_process():
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

    keys_to_process = get_keys_to_process()
    if not keys_to_process:
        print("All embeddings have already been processed.")
        sys.exit(0)
    else:
        print(f"{len(keys_to_process)} embeddings to process.")
    return keys_to_process

def handle_checkpoint(checkpoint_path):
    if checkpoint_path and checkpoint_path.is_file():
        print(f'Loading model checkpoint from {checkpoint_path}')
        return checkpoint_path

    default_checkpoint = Path('la_prott5_subcellular_localization.pt')
    if default_checkpoint.is_file():
        print(f'Using existing model checkpoint at {default_checkpoint}')
        return default_checkpoint

    print('Model checkpoint not provided or does not exist. Downloading...')
    weights_link = 'http://data.bioembeddings.com/public/embeddings/feature_models/light_attention/la_prott5_subcellular_localization.pt'
    download_file(weights_link, default_checkpoint)
    return default_checkpoint

def load_model(checkpoint_path, device):
    model = LightAttention(output_dim=10)
    state = torch.load(checkpoint_path, map_location=device)
    model.load_state_dict(state.get("model_state_dict", state))
    return model.eval().to(device)

def process_data(model, data_loader, output_path, device):
    with h5py.File(output_path, 'a') as h5_out:
        for batch_embs, batch_masks, header_list in tqdm(data_loader, desc='Processing batches'):
            batch_embs = batch_embs.to(device).float()
            batch_masks = batch_masks.to(device)
            intermediat_repr = process_batch(model, batch_embs, batch_masks)
            intermediat_repr = intermediat_repr.cpu().numpy()
            for header, embedding in zip(header_list, intermediat_repr):
                h5_out.create_dataset(header, data=embedding)
    print(f'Processing complete. Representations saved to {output_path}')

def download_file(url, destination):
    response = requests.get(url, stream=True)
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

class LightAttention(nn.Module):
    """LightAttention for subcellular localization prediction
    https://github.com/HannesStark/protein-localization/blob/master/models/light_attention.py
    """
    def __init__(
        self,
        embeddings_dim=1024,
        output_dim=11,
        dropout=0.25,
        kernel_size=9,
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

    def forward(self, x: torch.Tensor, mask, **kwargs) -> torch.Tensor:
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

        # --- Actual inference ---
        # o = self.feature_convolution(x)  # [batch_size, embeddings_dim, sequence_length]
        # o = self.dropout(o)  # [batch_size, embeddings_dim, sequence_length]
        # o1 = torch.sum(o * self.softmax(attention), dim=-1)  # [batchsize, embeddings_dim]
        # o1 = self.id1(o1)
        # o2, _ = torch.max(o, dim=-1)  # [batchsize, embeddings_dim]
        # o = torch.cat([o1, o2], dim=-1)  # [batchsize, 2*embeddings_dim]
        # o = self.id2(o)
        # o = self.linear(o)  # [batchsize, 32]
        # return self.output(o)  # [batchsize, output_dim]

        return extraction  # [batch_size, embeddings_dim]

def process_batch(model, batch_embs, batch_masks):
    with torch.no_grad():
        return model(batch_embs, batch_masks)

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
    emb_list, mask_list, key_list = zip(*batch)
    max_len = max(emb.shape[1] for emb in emb_list)
    batch_size = len(emb_list)
    emb_dim = emb_list[0].shape[0]

    batch_embs = torch.zeros(batch_size, emb_dim, max_len)
    batch_masks = torch.zeros(batch_size, max_len, dtype=torch.bool)

    for i, (emb, mask) in enumerate(zip(emb_list, mask_list)):
        seq_len = emb.shape[1]
        batch_embs[i, :, :seq_len] = emb
        batch_masks[i, :seq_len] = mask

    return batch_embs, batch_masks, key_list

if __name__ == '__main__':
    main()