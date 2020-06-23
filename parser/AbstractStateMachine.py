# -*- coding: utf-8 -*-


class AbstractStateMachineError(Exception):
    pass


class StateMachineInputError(AbstractStateMachineError):
    """Exception raised for errors in the input.

    Attributes:
        expression -- input expression in which the error occurred
        message -- explanation of the error
    """

    def __init__(self, message, pos):
        self.message = message
        self.pos = pos


class StateMachineTransitionError(AbstractStateMachineError):
    """Raised when an operation attempts a state transition that's not
    allowed.

    Attributes:
        previous -- state at beginning of transition
        next -- attempted new state
        message -- explanation of why the specific transition is not allowed
    """

    def __init__(self, old_state, new_state, pos):
        self.old_state = old_state
        self.new_state = new_state
        self.pos = pos


class AbstractStateMachine:
    """An AbstractStateMachine

    Attributes:
        debug -- The debug state
        pos -- The current position in the input
        symbol -- The current symbol at pos
        method -- The current state func to execute
        input -- The input object, must support enumerate()
        output -- The list of objects parsed
        dest -- The stack for recursive grammars
        depth -- The length of the dest stack minus one (an empty stack is -1)
        accum -- The accumulator
        state -- The current state name as a string

    """

    __version__ = '0.0.3'

    def __init__(self, source=None, start_state='normal', debug=False):
        """Initialise the State Machine
            Call this with super().__init__ when subclassing

        Attributes:
            start_state -- The inital state of the machine
            debug -- The debug state for this object
        """
        self.debug = debug
        self.pos = 0
        self.symbol = ''
        self.method = None
        self.input = source
        self.output = []
        self.dest = []
        self.accum = ''
        self.state = start_state
        self.lines = ['']

    @property
    def depth(self):
        """Returns the current stack depth with
            0 being the root object
            -1 completely empty stack
        """
        # return 0
        return len(self.dest) - 1

    def run(self):
        """Execute the state machine
            Each state func is found using getattr on the object

        Attributes:
            state_start -- Run before the state machine executes
            start_finish -- Run after the state machine finishes

        Returns:
            self.output -- the output list
        """
        start = getattr(self, 'state_start', None)
        if start:
            start()

        # transition into the initial state
        self.transition(self.state)

        for (self.pos, self.symbol) in enumerate(self.input):
            if self.symbol in '\n':
                self.lines.append('')
            else:
                self.lines[-1] += self.symbol
            self.method(self.symbol, self.pos)

        finish = getattr(self, 'state_finish', None)
        if finish:
            finish()

        return self.output

    def transition(self, new_state, clear_accum=True, tmp=None):
        """Transition from the current state to a new state

        Attributes:
            new_state -- the next state for the machine as a string
            clear_accum -- True if the accumulator should be cleared

        Notes:
            each state can have three funcs called with X(old_state, new_state)
            during transition

            state_X_enter -- run as we transition into a new state
            state_X_leave -- run as we transition out of the current state
            state_transition -- run whenever a transition is performed

            state_X -- the func for the new_state is stored in self.method

        Raises:
            StateMachineTransitionError if state_X cannot be found
        """

        if self.debug:
            print(
                '(line %4d) (line_pos %3d) (abs_pos %6d) (dep %4d) state %12s -> %12s sym \'%s\' accum \'%s\''
                % (len(self.lines), len(self.lines[-1]), self.pos, self.depth, self.state,
                   new_state, self.symbol, self.accum))
        leave = getattr(self, 'state_%s_leave' % (self.state), None)
        if leave:
            if self.debug:
                print('state_%s_leave %s -> %s' % (self.state, self.state, new_state))
            leave(old_state=self.state, new_state=new_state)
        enter = getattr(self, 'state_%s_enter' % (new_state), None)
        if enter:
            if self.debug:
                print('state_%s_enter %s -> %s' % (new_state, self.state, new_state))
            enter(old_state=self.state, new_state=new_state)
        trans = getattr(self, 'state_transition', None)
        if trans:
            if self.debug:
                print('state_transition %s -> %s' % (self.state, new_state))
            trans(old_state=self.state, new_state=new_state)

        if clear_accum:
            if self.debug:
                print('accumulator cleared')
            self.accum = ''
        else:
            if self.debug:
                print('accumulator: \'%s\'' % self.accum)

        self.tmp = tmp

        self.method = getattr(self, 'state_%s' % (new_state), None)
        if not self.method:
            raise StateMachineTransitionError(self.state, new_state, self.pos)
        self.state = new_state
        if self.debug:
            print('line \'%s\'' % self.lines[-1])

    def accumulate(self, c):
        """Accumulate a character into self.accum

        Attributes:
            c -- the symbol to accumulate
                we don't use self.symbol here as escapes might want to
                accumulate a different character
            accum -- the destination accumulator
        """

        # if self.debug:
        #     print('accumulate \'%s\' at %d onto \'%s\'' %
        #           (c, self.pos, self.accum))
        self.accum += c
