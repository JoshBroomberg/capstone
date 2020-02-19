"""This submodule contains the :class:`~maccabee.data_generation.generated_data_set.GeneratedDataSet` class which represents data sampled from :class:`~maccabee.data_generation.data_generating_process.DataGeneratingProcess` instances, providing the API used to interact with data sets generated by sampled or concrete DGPs.
"""

from ..constants import Constants
from ..exceptions import DGPVariableMissingException, UnknownDGPVariableException, UnknownEstimandException
import numpy as np
import pandas as pd
from functools import partial

DGPVariables = Constants.DGPVariables

class DGPVariableAccessor(type):
    DGP_VARIABLE_DICT_NAME = "DGP_VARIABLE_DICT"

    # This metaclass/type is used to programtically
    # inject attributes/methods corresponding to accessing DGP variables
    # into any class which intends to store generated DGP variables.

    @staticmethod
    def get_dgp_variable(instance, dgp_var_name):
        """get_dgp_variable(self, dgp_var_name)

        Returns the DGP variable given as `dgp_var_name`.

        Args:
            dgp_var_name (string): The name of a DGP variable from :class:`~maccabee.constants.Constants.DGPVariables`.

        Returns:
            object: the :class:`~pandas.DataFrame` or `numpy.ndarray` containing the DGP variable observations.

        Raises:
            UnknownDGPVariableException: if an unknown DGP variable is requested.
            DGPVariableMissingException: if the DGP variable was not generated by the DGP.
        """

        if dgp_var_name not in DGPVariables.all().values():
            raise UnknownDGPVariableException()

        dgp_var_dict = getattr(instance, DGPVariableAccessor.DGP_VARIABLE_DICT_NAME, None)
        if dgp_var_dict is None:
            raise DGPVariableMissingException(f"{instance} has not dgp variable data.")

        dgp_var_value = dgp_var_dict.get(dgp_var_name, None)
        if dgp_var_value is not None:
            return dgp_var_value
        else:
            raise DGPVariableMissingException(f"{dgp_var_name} not in generated data.")

    def __init__(cls, name, bases, clsdict):
        super(DGPVariableAccessor, cls).__init__(name, bases, clsdict)
        cls.DGP_VARIABLE_DICT_NAME = DGPVariableAccessor.DGP_VARIABLE_DICT_NAME
        for dgp_var_external_name, dgp_var_internal_name in DGPVariables.all().items():
            accessor_meth = partial(DGPVariableAccessor.get_dgp_variable, dgp_var_name=dgp_var_internal_name)
            accessor_meth.__doc__ = f"**[DGP VARIABLE]**\n\n This property accesses the DGP variable {dgp_var_internal_name} -  :class:`~maccabee.constants.Constants.DGPVariables.{dgp_var_external_name}`)"

            accessor_meth.__name__ = f"{dgp_var_internal_name}"
            setattr(cls, dgp_var_internal_name, property(accessor_meth))
            setattr(cls, "get_dgp_variable", DGPVariableAccessor.get_dgp_variable)

        return None

class GeneratedDataSet(metaclass=DGPVariableAccessor):
    """
    This class is used to interact with the data generated by Maccabee DGPs. It encapsulates the internal data structure produced by :class:`~maccabee.data_generation.data_generating_process.DataGeneratingProcess` instances and provides a clean (and field familiar) API which can be used to interact with the data sets sampled from DGPs.

    A :class:`~maccabee.data_generation.generated_data_set.GeneratedDataSet` instance provides access to two logically-distinct sets of variables via its attributes:

    * First, it provides access to all of the :term:`DGP variables <dgp variable>` which are generated by the DGP as attributes of the same name. This includes both :term:`observable <observable dgp variable>` and :term:`oracle <oracle dgp variable>` DGP variables. Note that these attributes, listed below, are named by the **value** of the constants in :class:`maccabee.constants.Constants.DGPVariables`. This is designed to aid in creating readable and succinct models. :func:`~maccabee.data_generation.data_generating_process.GeneratedDataSet.get_dgp_variable` can be used to access a DGP variable by name, thus allowing the use of the constant names (rather than values) in :class:`~maccabee.constants.Constants.DGPVariables`. These properties are marked with **[DGP VARIABLE]** below.


    * Second, it defines attributes which return ground-truth estimand values. These attributes are backed by functions which calculate the ground-truth values from the generated data. These properties are marked with **[ESTIMAND]** below.

    .. note::

      Behind the scenes, the DGP variable attributes are actually accessor functions which access the internal data structure to return the correct value for each DGP variable in :class:`~maccabee.constants.Constants.DGPVariables`. These functions are injected into the :class:`~maccabee.data_generation.generated_data_set.GeneratedDataSet` class through the ``DGPVariableAccessor(type)`` class which is used as type/metaclass for  :class:`~maccabee.data_generation.generated_data_set.GeneratedDataSet`. Users who plan to add their own DGP variables should see the source code and in line comments for the :class:`~maccabee.data_generation.data_generating_process.GeneratedDataSet` to ensure they understand this mechanism.
    """

    # TODO: write tooling to go to and from file to support static
    # benchmarking runs in future.

    # TODO: write tooling for convenient creation of GeneratedDataSet objects
    # from standard data frames.

    def __init__(self, dgp_variable_dict):
         setattr(self, self.DGP_VARIABLE_DICT_NAME, dgp_variable_dict)

    def _build_dataframe_for_vars(self, dgp_var_names):
        # Build a dataframe for the DGP variables listed in dgp_var_names.
        df = pd.DataFrame()
        for name in dgp_var_names:
            df[name] = self.get_dgp_variable(name)

        return df

    @property
    def observed_outcome_data(self):
        """
        **[DGP VARIABLE GROUP]**\n\n This property returns a DataFrame containing the observable outcome data: the treatment assignment and the observed outcome.
        """
        return self._build_dataframe_for_vars([
            DGPVariables.TREATMENT_ASSIGNMENT_NAME,
            DGPVariables.OBSERVED_OUTCOME_NAME
        ])

    @property
    def observed_data(self):
        """
        **[DGP VARIABLE GROUP]**\n\n This property returns a DataFrame containing all of the observable data: the observable covariates, the treatment assignment and the observed outcome. This is the data on which causal inference will be performed.
        """
        return self.X.join(self.observed_outcome_data)

    # Estimand accessors
    @property
    def ITE(self):
        """**[ESTIMAND]**\n\n This property accesses the ITE estimand"""
        return self.Y1 - self.Y0

    @property
    def ATE(self):
        """**[ESTIMAND]**\n\n This property accesses the ATE estimand"""
        return np.mean(self.ITE)

    @property
    def ATT(self):
        """**[ESTIMAND]**\n\n This property accesses the ATT estimand"""
        return np.mean(self.ITE.to_numpy()[self.T.to_numpy() == 1])

    def ground_truth(self, estimand):
        """Returns the ground truth for the estimand given in `estimand`.

        Args:
            estimand (string): An estimand from :class:`maccabee.constants.Constants.Model`

        Returns:
            float: the ground truth value for the given estimand.

        Raises:
            UnknownEstimandException: if an unknown estimand is supplied.
        """
        if estimand not in Constants.Model.ALL_ESTIMANDS:
            raise UnknownEstimandException()

        if not hasattr(self, estimand):
            raise NotImplementedError

        return getattr(self, estimand)
