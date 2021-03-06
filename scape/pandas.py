from __future__ import absolute_import
import pandas
from types import MethodType
from scape.registry import DataSource
#from scape.registry.tagged_dim import TaggedDim, tagged_dim
from scape.registry.table_metadata import create_table_field_tagged_dim_map
import scape.registry as reg
import functools

def datasource(readerf, metadata, description=None):
    """ Create a pandas data source 

    Args:
        readerf: Pandas DataFrame, or a function returning a Pandas DataFrame.
        metadata: :class:`scape.registry.TableMetadata` with metadata for the 
            DataFrame columns, or a dictionary in TableMetadata format.
    """
    md = create_table_field_tagged_dim_map(metadata)
    if hasattr(readerf,'__call__'):
        return _PandasDataFrameDataSource(readerf, md, description)
    elif isinstance(readerf, pandas.core.frame.DataFrame):
        return _PandasDataFrameDataSource(lambda:readerf, md, description)

_pandas_op_dict = {
    '==': reg.Equals,
    '!=': reg.NotEqual,
    '>': reg.GreaterThan,
    '>=': reg.GreaterThanEqualTo,
    '=~':  reg.MatchesCond,
   '<': reg.LessThan,
   '<=': reg.LessThanEqualTo
}

class _PandasDataFrameDataSource(DataSource):
    def __init__(self, readerf,  metadata, description):
        self._readerf = readerf
        desc = description if description else "Pandas DataSource"
        super(_PandasDataFrameDataSource, self).__init__(metadata, desc, _pandas_op_dict)

    def connect(self):
        if hasattr(self, '__dataframe'):
            return getattr(self, '__dataframe')
        """Load the associated DataFrame. """ 
        newdf = self._readerf()
        setattr(self, '__dataframe', newdf)
        return newdf

    def _go(self, cond):
        if not isinstance(cond, reg.Condition):
            raise ValueError("Expecting condition, not " + str(cond))
        df = self.connect()
        if isinstance(cond, reg.And):
            xs = cond._parts
            if len(xs)==0:
                raise ValueError("Empty And([])")
            if len(xs) == 1:
                return self._go(cond._parts[0])
            elif len(xs)>1:
                return functools.reduce(lambda x,y: x & self._go(y), xs[1:], self._go(xs[0]))
        elif isinstance(cond, reg.Or):
            xs = cond._parts
            if len(xs)==0:
                raise ValueError("Empty Or([])")
            elif len(xs)==1:
                return self._go(xs[0])
            elif len(xs)>1:
                return functools.reduce(lambda x,y: x | self._go(y), xs[1:], self._go(xs[0]))
        elif isinstance(cond, reg.Equals):
            return df[cond.lhs.name] == cond.rhs
        elif isinstance(cond, reg.NotEqual):
            return df[cond.lhs.name] != cond.rhs
        elif isinstance(cond, reg.GreaterThan):
            return df[cond.lhs.name] > cond.rhs
        elif isinstance(cond, reg.GreaterThanEqualTo):
            return df[cond.lhs.name] >= cond.rhs
        elif isinstance(cond, reg.LessThan):
            return df[cond.lhs.name] < cond.rhs
        elif isinstance(cond, reg.LessThanEqualTo):
            return df[cond.lhs.name] <= cond.rhs
        elif isinstance(cond, reg.MatchesCond):
            return df[cond.lhs.name].str.contains(cond.rhs)
        else:
            raise ValueError("Unexpected type {}".format(str(type(cond))))


    def _select_fields(self, df, select):
        if select.fields:
            return df[self._field_names(select)]
        else:
            return df

    def run(self, select):
        cond = self._rewrite(select.condition)
        df = self.connect()
        if isinstance(cond, reg.TrueCondition) or (isinstance(cond, reg.And) and not cond._parts):
            pass
        else:
            v = self._go(cond)
            df = df[v]
        return self._select_fields(df, select)

    def check_select(self, select):
        pass

    def check_query(self, cond):
        pass
