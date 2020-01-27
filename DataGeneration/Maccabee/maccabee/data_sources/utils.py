def random_covar_matrix(dimension, correlation_deg = 0.5):
    """
    Generate random covariance matrix by approximating the random
    vine method: https://stats.stackexchange.com/questions/2746/
    how-to-efficiently-generate-random-positive-semidefinite-correlation-matrices
    """
    if not (0 <= correlation_deg <= 1):
        raise Exception("Invalid correlation_deg. Must be in [0, 1]")

    # Small K means a larger degree of correlation.
    k = min(max(1, int(dimension*(1-correlation_deg))), dimension-1)
    W = np.random.normal(loc=0, scale=1, size=(dimension, k))
    S = W@W.T + np.diag(np.random.random(dimension))
    S = np.diag(1./np.sqrt(np.diag(S))) @ S @ np.diag(1./np.sqrt(np.diag(S)))

    return S

def load_covars_from_csv_path(covar_path):
    '''
    Fetches covariate data from the supplied path. This function expects
    a CSV file with column names in the first row.
    '''

    return pd.read_csv(covar_path)

def build_covar_data_frame(data, column_names, index):
    return pd.DataFrame(
            data=data,
            columns=column_names,
            index=index)
