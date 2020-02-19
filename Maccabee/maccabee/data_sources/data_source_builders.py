"""This module contains utility functions of the form ``build_*_datasource`` which provide a convenient way to instantiate :class:`DataSource <maccabee.data_sources.DataSource>` instances corresponding to commonly used/useful data sets."""

import numpy as np
import pandas as pd
from functools import partial

from ..constants import Constants

from .data_sources import StaticDataSource, StochasticDataSource
from .utils import random_covar_matrix, load_covars_from_csv_path, build_covar_data_frame


def build_csv_datasource(csv_path, discrete_covar_names):
    """Builds a datasource using the CSV of covariates at `csv_path`. This method expects a CSV with covariate names in the first row.

    Args:
        csv_path (string): The path to a CSV.
        discrete_covar_names (list): A list of string covariate names corresponding to the discrete covariates.

    Returns:
        :class:`DataSource <maccabee.data_sources.DataSource>`: A :class:`DataSource <maccabee.data_sources.DataSource>` instance which will generate the covariates from the CSV when sampled.
    """
    covar_names, covar_data = load_covars_from_csv_path(csv_path)

    return StaticDataSource(
        static_covar_data=covar_data,
        covar_names=covar_names,
        discrete_covar_names=discrete_covar_names)

def build_cpp_datasource():
    """Builds a datasource using the CPP data set of empirical covariates. See the theory paper for more on this data set.

    Returns:
        :class:`DataSource <maccabee.data_sources.DataSource>`: A :class:`DataSource <maccabee.data_sources.DataSource>` instance which will generate the covariates from the CPP data set when sampled.
    """
    return build_csv_datasource(
        Constants.ExternalCovariateData.CPP_PATH, Constants.ExternalCovariateData.CPP_DISCRETE_COVARS)

def build_lalonde_datasource():
    """Builds a datasource using the Lalonde data set of empirical covariates. See the theory paper for more on this data set.

    Returns:
        :class:`DataSource <maccabee.data_sources.DataSource>`: A :class:`DataSource <maccabee.data_sources.DataSource>` instance which will generate the covariates from the Lalonde data set when sampled.
    """
    return build_csv_datasource(
        Constants.ExternalCovariateData.LALONDE_PATH, Constants.ExternalCovariateData.LALONDE_DISCRETE_COVARS)

def build_random_normal_datasource(
    n_covars = 20, n_observations = 1000,
    partial_correlation_degree=0.0):
    """Builds a datasource using random normal covariates.

    Args:
        n_covars (int): The number of random normal covariates. Defaults to 20.
        n_observations (int): The number of observations in the data set. Defaults to 1000.
        partial_correlation_degree (float): The degree of partial correlation between the covariates. Full independance at ``0.0`` and perfect correlation at ``1.0``. A random covariance matrix is generated based on this parameter by approximating the random
        vine method. Defaults to 0.0.

    Returns:
        :class:`DataSource <maccabee.data_sources.DataSource>`: A :class:`DataSource <maccabee.data_sources.DataSource>` instance which will generate random normal covariates when sampled.

    .. _SO: https://stats.stackexchange.com/questions/2746/how-to-efficiently-generate-random-positive-semidefinite-correlation-matrices/
    """


    # Name covars sequentially
    covar_names = [f"X{i}" for i in range(n_covars)]

    gen_random_normal_data = partial(_gen_random_normal_data,
        n_covars, n_observations, partial_correlation_degree)

    return StochasticDataSource(
        covar_data_generator=gen_random_normal_data,
        covar_names=covar_names,
        discrete_covar_names=[])

def _gen_random_normal_data(n_covars, n_observations,
    correlation_deg):
    # Helper method which generates random normal data for the random normal data source builder.

    covar = random_covar_matrix(
        dimension=n_covars,
        correlation_deg=correlation_deg)

    # Generate standard normal random covariates
    covar_data = np.random.multivariate_normal(
        mean=np.full((n_covars,), 0),
        cov=1*covar,
        size=n_observations)

    return covar_data
