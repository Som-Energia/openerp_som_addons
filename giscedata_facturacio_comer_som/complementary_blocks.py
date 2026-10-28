"""Conservative presentation-only merging of complementary invoice blocks."""
from __future__ import absolute_import

from copy import deepcopy
from datetime import datetime, timedelta


class ComplementaryBlocks(list):
    """Keep original chart rounding boundaries outside public block dictionaries."""

    def __init__(self, blocks, originals):
        list.__init__(self, blocks)
        self.original_blocks = originals


def block_signature(block):
    metadata = []
    for key, value in sorted(block.items()):
        if isinstance(value, dict):
            metadata.append((key, tuple(sorted(
                (name, amount) for name, amount in value.items()
                if name not in ('quantity', 'price_subtotal', 'tolls', 'charges')))))
        elif key not in ('data_inici', 'data_fi', 'total'):
            metadata.append((key, value))
    return metadata


def merge_complementary_blocks(blocks, source_signatures):
    """None signatures mark uncertain or internally heterogeneous source groups."""
    if len(blocks) != len(source_signatures):
        return deepcopy(blocks)
    result = []
    previous_signature = None
    for block, signature in zip(blocks, source_signatures):
        current = deepcopy(block)
        adjacent = (result and
                    datetime.strptime(result[-1]['data_fi'], '%Y-%m-%d') +
                    timedelta(days=1) ==
                    datetime.strptime(current['data_inici'], '%Y-%m-%d'))
        if (adjacent and signature is not None and
                signature == previous_signature and
                block_signature(result[-1]) == block_signature(current)):
            target = result[-1]
            target['data_fi'] = current['data_fi']
            target['total'] += current['total']
            for period, values in current.items():
                if isinstance(values, dict):
                    for field in ('quantity', 'price_subtotal', 'tolls', 'charges'):
                        target[period][field] += values[field]
        else:
            result.append(current)
        previous_signature = signature
    if len(result) < len(blocks):
        return ComplementaryBlocks(result, deepcopy(blocks))
    return result
