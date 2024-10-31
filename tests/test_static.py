from calendar import c
import pytest

import sys
from copy import deepcopy


from ..xmt.recipes.static import parsing

class TestTags:
    def test_simple(self, sta):
        sta.execute()
        # simple tests
        assert sta._tags['all'] == [1, 2, 3]
        assert sta._tags['first'] == [1]
        assert sta._tags['last_two'] == [2, 3]
        # complex tests
        assert (~sta['all']).indices == []
        assert (sta['first'] | sta['last_two']).indices == [1, 2, 3]
    
    def test_special_simple(self, sta):
        sta.spec['content'].insert(0,
            {
                'tag': 'subsequent',
                'with': 'special-next'
            }
        )
        sta.spec['content'].insert(2,
            {
                'tag': 'preceding',
                'with': 'special-first'
            }
        )
        sta.spec['content'].append({
            'tag': 'preceding',
            'with': 'special-prev'
        })
        sta.execute()

        assert sta['special-next'].indices == [1, 2, 3]
        assert sta['special-prev'].indices == [1, 2, 3]
        assert sta['special-first'].indices == [1]


class TestInclude:
    # mark as expected failure
    def test_cyclic_dependency(self, sta):
        rec_lim = sys.getrecursionlimit()
        sys.setrecursionlimit(100)
        try:
            sta.spec['content'].append({'include': 'basic'})
            sta.execute()
        except RecursionError:
            pytest.fail('Cyclic dependency not caught.')
        except Exception:
            pass # succeded.
        finally:
            sys.setrecursionlimit(rec_lim)  # reset the recursion limit.

    def test_attachments_integration(self, sta):
        # set up the environment
        clone_spec = deepcopy(sta.spec)
        clone_spec['metadata']['id'] = 'dep'
        clone_spec['metadata']['name'] = 'dep'
        clone_spec['annotations'] = {
            'extra-comment': [
                'first comment from outside', 
                'second comment from outside', 
                'third']
        }

        # add the dependency
        sta.spec['content'].append({'include': 'dep'})
        sta.env['dep'] = clone_spec        # enough to initiate a clone
        sta.execute()

        # check the tags
        assert sta._tags['all'] == list(range(1, 7))
        assert sta._tags['first'] == [1, 4]
    
        # check the annotations: the attached ones should have extra comments.
        assert all('extra-comment' in sta[i] for i in [3, 4, 5])


class TestIndexStrings:
    @pytest.mark.parametrize('input, expected', [
        ('1..4', [1, 2, 3, 4]),
        ('8,9,10', [8, 9, 10]),
        ('1', [1])
    ])
    def test_simple(self, input, expected):
        assert parsing.parse_index_string(input, max(expected)) == expected
    @pytest.mark.parametrize('input, expected', [
        ('2,1,3,3,3', [1, 2, 3])
    ])
    def test_sort(self, input, expected):
        assert parsing.parse_index_string(input, max(expected)) == expected
    
    @pytest.mark.parametrize('input, expected', [
        ('1..4;5,6,7,8', [1, 2, 3, 4, 5, 6, 7, 8]),
        ('1..1', [1])
    ])
    def test_complex(self, input, expected):
        assert parsing.parse_index_string(input, max(expected)) == expected

    @pytest.mark.parametrize('input, total_len', [
        ('0..0', 1),
        ('4..3', 5),
        ('4..-1', 3),
        ('1..10/0', 12),
        ('1..10/-1', 12)
    ])
    def test_vacuous(self, input, total_len):
        # call parse_index_string. if an exception is raised, then the test passes.
        with pytest.raises(Exception):
            parsing.parse_index_string(input, total_len)
    
    @pytest.mark.parametrize('input, total_len, expected', [
        ('1..4/2', 4, [1, 3]),
        ('3..4/2', 4, [3]),
    ])
    def test_step(self, input, total_len, expected):
        assert parsing.parse_index_string(input, total_len) == expected
    
    @pytest.mark.parametrize('input, total_len, expected', [
        ('1..', 4, [1, 2, 3, 4]),
        ('..-1', 4, [1, 2, 3, 4]),
        ('..2', 4, [1, 2]),
        ('2../2', 4, [2, 4]),
        ('../1', 4, [1, 2, 3, 4]),
        ('../2', 4, [1, 3])
    ])
    def test_open_end(self, input, total_len, expected):
        assert parsing.parse_index_string(input, total_len) == expected


    def test_parsing_simple(self, sta):
        sta.spec['tags']['test-exp-first'] = 1
        sta.spec['tags']['test-exp-all'] = [1, 2, 3]
        sta.spec['tags']['test-imp-first'] = '1'
        sta.spec['tags']['test-imp-all'] = '1..3'
        
        sta.execute()

        assert sta.tags['test-exp-first'] == sta.tags['test-imp-first']
        assert sta.tags['test-exp-all'] == sta.tags['test-imp-all']
        assert sta.tags['test-exp-first'].indices == [1]
        assert sta.tags['test-exp-all'].indices == [1, 2, 3]