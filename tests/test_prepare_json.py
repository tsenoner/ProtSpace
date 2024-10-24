import h5py
import numpy as np
import pandas as pd
import pytest
from numpy.testing import assert_array_almost_equal
from scipy.spatial.distance import pdist, squareform

from protspace.utils.prepare_json import DataProcessor

# Constants
N_SAMPLES = 100
N_FEATURES = 50
RANDOM_SEED = 42

@pytest.fixture(scope="session")
def rng():
    """Provide a numpy random number generator with fixed seed."""
    return np.random.RandomState(RANDOM_SEED)

@pytest.fixture(scope="session")
def headers():
    """Generate consistent headers for all tests."""
    return [f"protein_{i:03d}" for i in range(N_SAMPLES)]

@pytest.fixture(scope="session")
def structured_embeddings(rng):
    """Create embeddings with clear cluster structure."""
    cluster_centers = rng.randn(3, N_FEATURES)
    return np.vstack([
        cluster_centers[0] + 0.1 * rng.randn(34, N_FEATURES),
        cluster_centers[1] + 0.1 * rng.randn(33, N_FEATURES),
        cluster_centers[2] + 0.1 * rng.randn(33, N_FEATURES)
    ])

@pytest.fixture(scope="session")
def single_cluster_embeddings(rng, structured_embeddings):
    """Create embeddings with all points very close together."""
    center = structured_embeddings[0]
    return center + 0.001 * rng.randn(N_SAMPLES, N_FEATURES)

@pytest.fixture(scope="session")
def metadata(headers, rng):
    """Create structured metadata matching the clusters."""
    return pd.DataFrame({
        'identifier': headers,
        'group': np.repeat(['A', 'B', 'C'], [34, 33, 33]),
        'value': rng.rand(N_SAMPLES),
        'integer': rng.randint(1, 100, N_SAMPLES),
        'category': rng.choice(['high', 'medium', 'low'], N_SAMPLES),
        'binary': rng.choice([0, 1], N_SAMPLES)
    })

@pytest.fixture(scope="session")
def partial_metadata(metadata):
    """Create partial metadata (every other row)."""
    return metadata.iloc[::2].copy()

@pytest.fixture(scope="session")
def sparse_metadata(metadata, rng):
    """Create metadata with some NaN values."""
    sparse = metadata.copy()
    sparse.loc[::3, ['value', 'category']] = np.nan
    return sparse

@pytest.fixture(scope="session")
def similarity_matrices(structured_embeddings):
    """Create different types of similarity matrices."""
    euclidean = squareform(pdist(structured_embeddings))
    cosine = 1 - squareform(pdist(structured_embeddings, metric='cosine'))
    return {'euclidean': euclidean, 'cosine': cosine}

@pytest.fixture(scope="session")
def tmp_dir(tmp_path_factory):
    """Create a temporary directory for test files."""
    return tmp_path_factory.mktemp("test_data")

@pytest.fixture(scope="session")
def test_files(tmp_dir, headers, structured_embeddings, single_cluster_embeddings,
               similarity_matrices, metadata, partial_metadata, sparse_metadata, rng):
    """Create and save all test files."""
    files = {}

    # Save embeddings (shuffled order)
    shuffled_indices = np.random.permutation(N_SAMPLES)
    shuffled_headers = [headers[i] for i in shuffled_indices]

    # Regular embeddings
    files['embeddings'] = tmp_dir / 'embeddings.hdf5'
    with h5py.File(files['embeddings'], 'w') as f:
        for header, idx in zip(shuffled_headers, shuffled_indices):
            f.create_dataset(header, data=structured_embeddings[idx])

    # Single cluster embeddings
    files['single_cluster'] = tmp_dir / 'single_cluster.hdf5'
    with h5py.File(files['single_cluster'], 'w') as f:
        for header, emb in zip(headers, single_cluster_embeddings):
            f.create_dataset(header, data=emb)

    # Similarity matrices
    for name, matrix in similarity_matrices.items():
        path = tmp_dir / f'similarity_{name}.csv'
        pd.DataFrame(matrix, index=headers, columns=headers).to_csv(path)
        files[f'similarity_{name}'] = path

    # Metadata files
    files['metadata'] = tmp_dir / 'metadata.csv'
    metadata.to_csv(files['metadata'], index=False)

    files['partial_metadata'] = tmp_dir / 'partial_metadata.csv'
    partial_metadata.to_csv(files['partial_metadata'], index=False)

    files['sparse_metadata'] = tmp_dir / 'sparse_metadata.csv'
    sparse_metadata.to_csv(files['sparse_metadata'], index=False)

    # Invalid files
    files['invalid_sim'] = tmp_dir / 'invalid_sim.csv'
    invalid_sim = pd.DataFrame(
        similarity_matrices['euclidean'][:50],
        index=headers[:50],
        columns=headers
    )
    invalid_sim.to_csv(files['invalid_sim'])

    files['invalid_metadata'] = tmp_dir / 'invalid_metadata.csv'
    metadata.drop('identifier', axis=1).to_csv(files['invalid_metadata'], index=False)

    # Empty and malformed files
    files['empty'] = tmp_dir / 'empty.csv'
    pd.DataFrame().to_csv(files['empty'])

    files['malformed'] = tmp_dir / 'malformed.csv'
    with open(files['malformed'], 'w') as f:
        f.write("malformed,csv\ndata,")

    return files

@pytest.fixture
def processor():
    """Create a DataProcessor instance."""
    return DataProcessor({'random_state': RANDOM_SEED})

def test_load_embeddings_ordering(processor, test_files, headers, structured_embeddings):
    """Test that embeddings are properly reordered regardless of HDF storage order."""
    metadata, data, loaded_headers = processor.load_data(
        test_files['embeddings'],
        test_files['metadata']
    )

    assert loaded_headers == headers
    expected_embeddings = structured_embeddings[
        [headers.index(h) for h in loaded_headers]
    ]
    assert_array_almost_equal(data, expected_embeddings)

@pytest.mark.parametrize("sim_type", ["euclidean", "cosine"])
def test_load_similarity(processor, test_files, headers, similarity_matrices, sim_type):
    """Test loading different types of similarity matrices."""
    metadata, data, loaded_headers = processor.load_data(
        test_files[f'similarity_{sim_type}'],
        test_files['metadata']
    )

    assert loaded_headers == headers
    expected_similarity = similarity_matrices[sim_type]
    assert_array_almost_equal(data, expected_similarity)

def test_partial_metadata(processor, test_files):
    """Test handling of partial metadata."""
    metadata, data, headers = processor.load_data(
        test_files['embeddings'],
        test_files['partial_metadata']
    )

    assert len(headers) == N_SAMPLES
    assert metadata['value'].isna().any()

def test_invalid_similarity(processor, test_files):
    """Test handling of invalid similarity matrix."""
    with pytest.raises(ValueError, match="matching row and column"):
        processor.load_data(test_files['invalid_sim'], test_files['metadata'])

@pytest.mark.parametrize("method,metric", [
    ('umap', 'euclidean'),
    ('umap', 'cosine'),
    ('tsne', 'euclidean'),
    ('tsne', 'cosine')
])
def test_different_metrics(processor, test_files, method, metric):
    """Test reduction methods with different distance metrics."""
    processor = DataProcessor({'random_state': RANDOM_SEED, 'metric': metric})

    metadata, data, headers = processor.load_data(
        test_files['embeddings'],
        test_files['metadata']
    )
    result = processor.process_reduction(data, method, 2)
    assert result['info']['metric'] == metric

@pytest.mark.parametrize("method", ['pca', 'mds'])
def test_cluster_preservation(processor, test_files, method):
    """Test that reduction methods preserve cluster structure."""
    metadata, data, headers = processor.load_data(
        test_files['embeddings'],
        test_files['metadata']
    )

    result = processor.process_reduction(data, method, 2)
    reduced_data = result['data']

    # Calculate intra and inter cluster distances
    group_assignments = metadata['group'].values
    intra_cluster_dist = []
    inter_cluster_dist = []

    for i in range(len(reduced_data)):
        for j in range(i + 1, len(reduced_data)):
            dist = np.linalg.norm(reduced_data[i] - reduced_data[j])
            if group_assignments[i] == group_assignments[j]:
                intra_cluster_dist.append(dist)
            else:
                inter_cluster_dist.append(dist)

    assert np.mean(intra_cluster_dist) < np.mean(inter_cluster_dist)

@pytest.mark.parametrize("method", ['pca', 'mds'])
def test_single_cluster(processor, test_files, method):
    """Test behavior with nearly identical points."""
    metadata, data, headers = processor.load_data(
        test_files['single_cluster'],
        test_files['metadata']
    )

    result = processor.process_reduction(data, method, 2)
    reduced_data = result['data']
    max_dist = np.max(pdist(reduced_data))

    assert max_dist < 1.0

def test_sparse_metadata_handling(processor, test_files, sparse_metadata):
    """Test handling of sparse metadata with many NaN values."""
    metadata, data, headers = processor.load_data(
        test_files['embeddings'],
        test_files['sparse_metadata']
    )

    assert metadata['value'].isna().any()
    assert metadata['category'].isna().any()

    non_nan_idx = ~metadata['value'].isna()
    pd.testing.assert_series_equal(
        metadata.loc[non_nan_idx, 'value'],
        sparse_metadata.loc[non_nan_idx, 'value']
    )

@pytest.mark.parametrize("input_type,meta_type", [
    ('embeddings', 'metadata'),
    ('similarity_euclidean', 'partial_metadata'),
    ('similarity_cosine', 'sparse_metadata')
])
def test_output_consistency(processor, test_files, headers, input_type, meta_type):
    """Test consistency of output format with various inputs."""
    metadata, data, loaded_headers = processor.load_data(
        test_files[input_type],
        test_files[meta_type]
    )

    reductions = []
    for method in ['pca', 'mds']:
        result = processor.process_reduction(data, method, 2)
        reductions.append(result)

    output = processor.create_output(metadata, reductions, loaded_headers)

    assert 'protein_data' in output
    assert 'projections' in output
    assert set(output['protein_data'].keys()) == set(headers)

    for proj in output['projections']:
        proj_ids = {item['identifier'] for item in proj['data']}
        assert proj_ids == set(headers)

def test_deterministic_results(processor, test_files):
    """Test that results are deterministic with same random_state."""
    metadata, data, headers = processor.load_data(
        test_files['embeddings'],
        test_files['metadata']
    )

    result1 = processor.process_reduction(data, 'pca', 2)
    result2 = processor.process_reduction(data, 'pca', 2)

    assert_array_almost_equal(result1['data'], result2['data'])

@pytest.mark.parametrize("error_file", ['empty', 'malformed', 'nonexistent.csv'])
def test_error_handling(processor, test_files, error_file):
    """Test error handling for various edge cases."""
    if error_file == 'nonexistent.csv':
        error_path = test_files['metadata'].parent / error_file
    else:
        error_path = test_files[error_file]

    metadata, data, headers = processor.load_data(
        test_files['embeddings'],
        error_path
    )

    assert len(metadata.columns) == 1
    assert len(headers) == N_SAMPLES