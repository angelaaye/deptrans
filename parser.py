#!/usr/bin/env python3
"""Functions and classes that handle parsing"""

from itertools import chain
from nltk.parse import DependencyGraph


class PartialParse(object):
    """A PartialParse is a snapshot of an arc-standard dependency parse

    It is fully defined by a quadruple (sentence, stack, next, arcs).

    sentence is a tuple of ordered pairs of (word, tag), where word
    is a a word string and tag is its part-of-speech tag.

    Index 0 of sentence refers to the special "root" node
    (None, self.root_tag). Index 1 of sentence refers to the sentence's
    first word, index 2 to the second, etc.

    stack is a list of indices referring to elements of
    sentence. The 0-th index of stack should be the bottom of the stack,
    the (-1)-th index is the top of the stack (the side to pop from).

    next is the next index that can be shifted from the buffer to the
    stack. When next == len(sentence), the buffer is empty.

    arcs is a list of triples (idx_head, idx_dep, deprel) signifying the
    dependency relation `idx_head ->_deprel idx_dep`, where idx_head is
    the index of the head word, idx_dep is the index of the dependant,
    and deprel is a string representing the dependency relation label.
    """

    left_arc_id = 0
    """An identifier signifying a left arc transition"""

    right_arc_id = 1
    """An identifier signifying a right arc transition"""

    shift_id = 2
    """An identifier signifying a shift transition"""

    root_tag = "TOP"
    """A POS-tag given exclusively to the root"""

    def __init__(self, sentence):
        # the initial PartialParse of the arc-standard parse
        # **DO NOT ADD ANY MORE ATTRIBUTES TO THIS OBJECT**
        self.sentence = ((None, self.root_tag),) + tuple(sentence)
        self.stack = [0]
        self.next = 1
        self.arcs = []

    @property
    def complete(self):
        """bool: return true iff the PartialParse is complete

        Assume that the PartialParse is valid
        """
        # *** BEGIN YOUR CODE ***
        if self.next == len(self.sentence) and self.stack == [0]:
            return True
        return False
        # *** END YOUR CODE ***

    def parse_step(self, transition_id, deprel=None):
        """Update the PartialParse with a transition

        Args:
            transition_id : int
                One of left_arc_id, right_arc_id, or shift_id. You
                should check against `self.left_arc_id`,
                `self.right_arc_id`, and `self.shift_id` rather than
                against the values 0, 1, and 2 directly.
            deprel : str or None
                The dependency label to assign to an arc transition
                (either a left-arc or right-arc). Ignored if
                transition_id == shift_id

        Raises:
            ValueError if transition_id is an invalid id or is illegal
                given the current state
        """
        # *** BEGIN YOUR CODE ***
        if transition_id == self.left_arc_id:
            if len(self.stack) >= 2:
                # pop the second last index, find the dependent word
                dependent = self.stack.pop(-2)
                self.arcs.append((self.stack[-1], dependent, deprel))
            else:
                raise ValueError('Invalid ID: Stack must contain at least 2 elements for left-arc')

        elif transition_id == self.right_arc_id:
            if len(self.stack) >= 2:
                # pop the last index, find the dependent word
                dependent = self.stack.pop()
                self.arcs.append((self.stack[-1], dependent, deprel))
            else:
                raise ValueError('Invalid ID: Stack must contain at least 2 elements for right-arc')

        elif transition_id == self.shift_id:
            if self.next < len(self.sentence):
                self.stack.append(self.next)
                self.next += 1
            else:
                raise ValueError('Invalid ID: The next element is outside of sentence range for shift')

        else:
            raise ValueError('Invalid ID: Must choose from 0, 1, or 2')

        # *** END YOUR CODE ***

    def get_n_leftmost_deps(self, sentence_idx, n=None):
        """Returns a list of n leftmost dependants of word

        Leftmost means closest to the beginning of the sentence.

        Note that only the direct dependants of the word on the stack
        are returned (i.e. no dependants of dependants).

        Args:
            sentence_idx : refers to word at self.sentence[sentence_idx]
            n : the number of dependants to return. "None" refers to all
                dependants

        Returns:
            deps : The n leftmost dependants as sentence indices.
                If fewer than n, return all dependants. Return in order
                with the leftmost @ 0, immediately right of leftmost @
                1, etc.
        """
        # *** BEGIN YOUR CODE ***
        deps = []
        if n == 0:
            return deps
        if not n:
            n = len(self.sentence)
        for tup in self.arcs:
            idx_head, idx_dep, _ = tup
            if idx_head == sentence_idx:
                deps.append(idx_dep)
        deps.sort()  # sort from smallest index to largest (leftmost first)
        deps = deps[:n]
        # *** END YOUR CODE ***
        return deps

    def get_n_rightmost_deps(self, sentence_idx, n=None):
        """Returns a list of n rightmost dependants of word on the stack @ idx

        Rightmost means closest to the end of the sentence.

        Note that only the direct dependants of the word on the stack
        are returned (i.e. no dependants of dependants).

        Args:
            sentence_idx : refers to word at self.sentence[sentence_idx]
            n : the number of dependants to return. "None" refers to all
                dependants

        Returns:
            deps : The n rightmost dependants as sentence indices. If
                fewer than n, return all dependants. Return in order
                with the rightmost @ 0, immediately left of leftmost @
                1, etc.
        """
        # *** BEGIN YOUR CODE ***
        deps = []
        if n == 0:
            return deps
        if not n:
            n = len(self.sentence)
        for tup in self.arcs:
            idx_head, idx_dep, _ = tup
            if idx_head == sentence_idx:
                deps.append(idx_dep)
        deps.sort(reverse=True)  # sort from largest index to smallest (rightmost first)
        deps = deps[:n]
        # *** END YOUR CODE ***
        return deps

    def get_oracle(self, graph):
        """Given a projective dependency graph, determine an appropriate trans

        This method chooses either a left-arc, right-arc, or shift so
        that, after repeated calls to pp.parse_step(*pp.get_oracle(graph)),
        the arc-transitions this object models matches the
        DependencyGraph "graph". For arcs, it also has to pick out the
        correct dependency relationship.

        Some relevant details about graph:
         - graph.nodes[i] corresponds to self.sentence[i]
         - graph.nodes[i]['head'] is either the i-th word's head word or
           None if i is the root word (i == 0)
         - graph.nodes[i]['deps'] returns a dictionary of arcs whose
           keys are dependency relationships and values are lists of
           indices of dependents. For example, given the list
           `dependents = graph.nodes[i]['deps']['det']`, the following
           arc transitions exist:
             self.sentences[i] ->_'det' self.sentences[dependents[0]]
             self.sentences[i] ->_'det' self.sentences[dependents[1]]
             ... (etc.)
         - graph is projective. Informally, this means no crossed lines
           in the dependency graph.
           More formally, if i -> j and j -> k, then:
             if i > j (left-ark), i > k
             if i < j (right-ark), i < k

        *IMPORTANT* if left-arc and shift operations are both valid and
        can lead to the same graph, always choose the left-arc
        operation.

        *ALSO IMPORTANT* make sure to use the values `self.left_arc_id`,
        `self.right_arc_id`, `self.shift_id` rather than 0, 1, and 2
        directly

        Hint: take a look at get_left_deps and get_right_deps below

        Args:
            graph : nltk.parse.dependencygraph.DependencyGraph
                A projective dependency graph to head towards

        Returns:
            transition_id, deprel : the next transition to take, along
                with the correct dependency relation label

        Raises:
            ValueError if already completed. Otherwise you can always
            assume that a valid move exists that heads towards the
            target graph
        """
        if self.complete:
            raise ValueError('PartialParse already completed')
        transition_id, deprel = -1, None
        # *** BEGIN YOUR CODE ***
        # If only root node is in the stack
        if len(self.stack) == 1:
            transition_id, deprel = self.shift_id, None
        else: # two or more nodes, can perform any of left/right/shift
            first_ind = self.stack[-1]
            second_ind = self.stack[-2]
            # first check if left-arc is possible
            if graph.nodes[second_ind]['head'] == first_ind:
                # can perform left-arc because the second element is a dependent of the first
                # use the "rel" key, which gives the deprel of the dependent
                transition_id, deprel = self.left_arc_id, graph.nodes[second_ind]['rel']
            # now check if right-arc is possible
            elif graph.nodes[first_ind]['head'] == second_ind:
                # can only perform right-arc if the first element is a dependent of the second
                # AND the first element does not have other right-arc dependencies
                shifted = False
                for val in graph.nodes[first_ind]['deps'].values():
                    for v in val:
                        # check if there is still a right-arc dependent that has not been used yet
                        if v >= self.next:
                            transition_id, deprel = self.shift_id, None
                            shifted = True
                            break
                if not shifted:
                    transition_id, deprel = self.right_arc_id, graph.nodes[first_ind]['rel']
            else:  # can only shift
                transition_id, deprel = self.shift_id, None
        # *** END YOUR CODE ***
        return transition_id, deprel

    def parse(self, td_pairs):
        """Applies the provided transitions/deprels to this PartialParse

        Simply reapplies parse_step for every element in td_pairs

        Args:
            td_pairs:
                The list of (transition_id, deprel) pairs in the order
                they should be applied
        Returns:
            The list of arcs produced when parsing the sentence.
            Represented as a list of tuples where each tuple is of
            the form (head, dependent)
        """
        for transition_id, deprel in td_pairs:
            self.parse_step(transition_id, deprel)
        return self.arcs


def minibatch_parse(sentences, model, batch_size):
    """Parses a list of sentences in minibatches using a model.

    Note that parse_step may raise a ValueError if your model predicts
    an illegal (transition, label) pair. Remove any such `stuck`
    partial-parses from the list unfinished_parses.

    Args:
        sentences:
            A list of "sentences", where each elemenent is itself a
            list of pairs of (word, pos)
        model:
            The model that makes parsing decisions. It is assumed to
            have a function model.predict(partial_parses) that takes in
            a list of PartialParse as input and returns a list of
            pairs of (transition_id, deprel) predicted for each parse.
            That is, after calling
                td_pairs = model.predict(partial_parses)
            td_pairs[i] will be the next transition/deprel pair to apply
            to partial_parses[i].
        batch_size:
            The number of PartialParse to include in each minibatch
    Returns:
        arcs:
            A list where each element is the arcs list for a parsed
            sentence. Ordering should be the same as in sentences (i.e.,
            arcs[i] should contain the arcs for sentences[i]).
    """
    # *** BEGIN YOUR CODE ***
    arcs = []
    # list of partial_parses, one for each sentence
    partial_parses = [PartialParse(s) for s in sentences]
    # shallow copy
    unfinished_parses = partial_parses[:]
    while unfinished_parses:
        # take parses in batches and use the model to predict the next transition for each partial batch
        minibatch = unfinished_parses[:batch_size]
        td_pairs = model.predict(minibatch)
        for i in range(len(minibatch)):
            # perform a parse step on each partial parse in the minibatch with its predicted transition
            try:
                minibatch[i].parse([td_pairs[i]])
            except (ValueError): # remove stuck parses
                arcs.append(minibatch[i].arcs)
                unfinished_parses.remove(minibatch[i])
    # *** END YOUR CODE ***
    return arcs


# *** HELPER FUNCTIONS (look here!) ***


def get_sentence_from_graph(graph, include_root=False):
    """Get the associated sentence from a DependencyGraph"""
    sentence_w_addresses = [(node['address'], node['word'], node['ctag'])
                            for node in graph.nodes.values()
                            if include_root or node['word'] is not None]
    sentence_w_addresses.sort()
    return tuple(t[1:] for t in sentence_w_addresses)


def get_deps(node):
    """Get the indices of dependants of a node from a DependencyGraph"""
    return chain(*node['deps'].values())


def get_left_deps(node):
    """Get the arc-left dependants of a node from a DependencyGraph"""
    # address == graph key
    return (dep for dep in get_deps(node) if dep < node['address'])


def get_right_deps(node):
    """Get the arc-right dependants of a node from a DependencyGraph"""
    return (dep for dep in get_deps(node) if dep > node['address'])


# *** TESTING ***


class DummyModel(object):
    """Dummy model for testing the minibatch_parse function

    First shifts everything onto the stack. If the first word of the
    sentence is not 'left', arc-right until completion. Otherwise,
    arc-left will be performed until only the root and one other word
    are on the stack, at which point it'll have to be an arc-right.

    Always gives the dependency relation label 'deprel'
    """

    def predict(self, partial_parses):
        ret = []
        for pp in partial_parses:
            if pp.next < len(pp.sentence):
                ret.append((pp.shift_id, 'deprel'))
            elif pp.sentence[1][0] == 'left' and len(pp.stack) != 2:
                ret.append((pp.left_arc_id, 'deprel'))
            else:
                ret.append((pp.right_arc_id, 'deprel'))
        return ret


def _test_arcs(name, pp, ex_arcs):
    """Tests the provided arcs match the expected arcs"""
    arcs = tuple(sorted(pp.arcs))
    ex_arcs = tuple(sorted(ex_arcs))
    assert arcs == ex_arcs, \
        "{} test resulted in arc list {}, expected {}".format(
            name,
            [(pp.sentence[arc[0]], pp.sentence[arc[1]], arc[2])
             for arc in arcs],
            [(pp.sentence[arc[0]], pp.sentence[arc[1]], arc[2])
             for arc in ex_arcs]
            )


def _test_stack(name, pp, ex_stack):
    """Test that the provided stack matches the expected stack"""
    stack = tuple(pp.stack)
    ex_stack = tuple(ex_stack)
    assert stack == ex_stack, \
        "{} test resulted in stack {}, expected {}".format(
            name,
            [pp.sentence[x] for x in stack],
            [pp.sentence[x] for x in ex_stack]
            )


def _test_next(name, pp, ex_next):
    """Test that the next (buffer) pointer matches the expected pointer"""
    assert pp.next == ex_next, \
        "{} test resulted in next {}, expected {}".format(
            name, pp.sentence[pp.next], pp.sentence[ex_next])


def _test_deps(name, pp, stack_idx, n, ex_deps, left=True):
    """Test that dependants list of size n matches the expected deps"""
    if left:
        deps = pp.get_n_leftmost_deps(stack_idx, n=n)
    else:
        deps = pp.get_n_rightmost_deps(stack_idx, n=n)
    assert tuple(deps) == tuple(ex_deps), \
        "{} test resulted in dependants {}, expected {}".format(
            name,
            [pp.sentence[x] for x in deps],
            [pp.sentence[x] for x in ex_deps],
        )
    print("{} test passed!".format(name))


def _test_parse_step(
        name, transition_id, label,
        stack_init, next_init, arcs_init,
        ex_stack, ex_next, ex_arcs):
    """Tests that a single parse step returns the expected output"""
    pp = PartialParse(
        [('word_' + str(x), 'tag_' + str(x)) for x in range(100)])
    pp.stack, pp.next, pp.arcs = stack_init, next_init, arcs_init
    pp.parse_step(transition_id, label)
    _test_stack(name, pp, ex_stack)
    _test_next(name, pp, ex_next)
    _test_arcs(name, pp, ex_arcs)
    print("{} test passed!".format(name))


def test_leftmost_rightmost():
    """Simple tests for the PartialParse.get_n_leftmost_deps and rightmost
    Warning: these are not exhaustive
    """
    pp = PartialParse(
        [('word_' + str(x), 'tag_' + str(x)) for x in range(100)])
    pp.stack = [0, 2, 4, 8]
    pp.next = 10
    pp.arcs = [(0, 1, 'a'),
               (4, 3, 'b'),
               (4, 5, 'c'),
               (4, 6, 'd'),
               (8, 7, 'e'),
               (8, 9, 'f'),
               ]
    _test_deps("0 leftmost (all)", pp, 0, None, (1,))
    _test_deps("0 rightmost (1)", pp, 0, 1, (1,), False)
    _test_deps("2 leftmost (10)", pp, 2, 10, tuple())
    _test_deps("2 rightmost (all)", pp, 2, None, tuple(), False)
    _test_deps("4 leftmost (0)", pp, 4, 0, tuple())
    _test_deps("4 leftmost (2)", pp, 4, 2, (3, 5))
    _test_deps("4 leftmost (4)", pp, 4, 4, (3, 5, 6))
    _test_deps("4 rightmost (2)", pp, 4, 2, (6, 5), False)


def test_parse_steps():
    """Simple tests for the PartialParse.parse_step function
    Warning: these are not exhaustive
    """
    _test_parse_step('shift', PartialParse.shift_id, 'tingle', [0, 1], 2, [],
                     [0, 1, 2], 3, [])
    _test_parse_step('left-arc', PartialParse.left_arc_id, 'tingle', [0, 1, 2],
                     3, [], [0, 2], 3, [(2, 1, 'tingle')])
    _test_parse_step('right-arc', PartialParse.right_arc_id, 'koolimpah',
                     [0, 1, 2], 3, [], [0, 1], 3, [(1, 2, 'koolimpah')])


def test_parse():
    """Simple tests for the PartialParse.parse function
    Warning: these are not exhaustive
    """
    sentence = tuple(('word_' + str(x), 'tag_' + str(x)) for x in range(1, 4))
    pp = PartialParse(sentence)
    assert not pp.complete, "PartialParse should not be complete yet"
    arcs = pp.parse([(pp.shift_id, None),
                     (pp.shift_id, None),
                     (pp.shift_id, None),
                     (pp.left_arc_id, 'a'),
                     (pp.right_arc_id, 'b'),
                     (pp.right_arc_id, 'c'),
                     ])
    _test_arcs("parse", pp, ((0, 1, 'c'), (1, 3, 'b'), (3, 2, 'a')))
    _test_stack("parse", pp, [0])
    _test_next("parse", pp, 4)
    assert pp.complete, "PartialParse should be complete by now"
    print("parse test passed!")


def test_minibatch_parse():
    """Simple tests for the minibatch_parse function
    Warning: these are not exhaustive
    """
    sentences = [[('right', 'a'),
                  ('arcs', 'b'),
                  ('only', 'c')],
                 [('right', 'd'),
                  ('arcs', 'e'),
                  ('only', 'f'),
                  ('again', 'g')],
                 [('left', 'h'),
                  ('arcs', 'i'),
                  ('only', 'j')],
                 [('left', 'k'),
                  ('arcs', 'l'),
                  ('only', 'm'),
                  ('again', 'n')],
                 ]
    arcs = minibatch_parse(sentences, DummyModel(), 2)
    # bludgeon the arcs into PartialParse to remain compatible with _test_arcs
    partial_parses = []
    for sentence, sentence_arcs in zip(sentences, arcs):
        pp = PartialParse(sentence)
        pp.arcs = sentence_arcs
        partial_parses.append(pp)
    _test_arcs("minibatch_parse[0]", partial_parses[0],
               [(0, 1, 'deprel'), (1, 2, 'deprel'), (2, 3, 'deprel')])
    _test_arcs("minibatch_parse[1]", partial_parses[1],
               [(0, 1, 'deprel'), (1, 2, 'deprel'), (2, 3, 'deprel'),
                (3, 4, 'deprel')])
    _test_arcs("minibatch_parse[2]", partial_parses[2],
               [(0, 3, 'deprel'), (3, 1, 'deprel'), (3, 2, 'deprel')])
    _test_arcs("minibatch_parse[3]", partial_parses[3],
               [(0, 4, 'deprel'), (4, 1, 'deprel'), (4, 2, 'deprel'),
                (4, 3, 'deprel')])
    print("minibatch_parse test passed!")


def test_oracle():
    """Make sure that the oracle is able to build the correct arcs in order"""
    graph_data = """\
word_1 tag_1 0 ROOT
word_2 tag_2 3 deprel_2
word_3 tag_3 5 deprel_3
word_4 tag_4 3 deprel_4
word_5 tag_5 1 deprel_5
"""
    graph = DependencyGraph(graph_data)
    pp = PartialParse(get_sentence_from_graph(graph))
    transition_ids = []
    while not pp.complete:
        transition_id, deprel = pp.get_oracle(graph)
        transition_ids.append(transition_id)
        pp.parse_step(transition_id, deprel)
    _test_arcs("oracle", pp,
               [(0, 1, 'ROOT'), (3, 2, 'deprel_2'), (5, 3, 'deprel_3'),
                (3, 4, 'deprel_4'), (1, 5, 'deprel_5')]
               )
    ex_tids = [pp.shift_id, pp.shift_id, pp.shift_id,  # 0 1 2 3
               pp.left_arc_id, pp.shift_id,  # 0 1 3 4
               pp.right_arc_id, pp.shift_id,  # 0 1 3 5
               pp.left_arc_id,  # 0 1 5
               pp.right_arc_id, pp.right_arc_id,  # 0
               ]
    assert transition_ids == ex_tids, \
        "oracle test resulted in transitions {}, expected {}".format(
            transition_ids, ex_tids)
    print('oracle test passed!')


if __name__ == '__main__':
    test_parse_steps()
    test_parse()
    test_leftmost_rightmost()
    test_minibatch_parse()
    test_oracle()
