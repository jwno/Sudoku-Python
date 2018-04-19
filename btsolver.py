import filereader
import gameboard
import variable
import domain
import trail
import constraint
import constraintnetwork
import time

# dictionary mapping heuristic to number
'''

for example, to set the variable selection heuristic to MRV,
you would say,
self.setVariableSelectionHeuristic(VariableSelectionHeuristic['MinimumRemainingValue'])
this is needed when you have more than one heuristic to break ties or use one over the other in precedence.
you can also manually set the heuristics in the main.py file when reading the parameters
as the primary heuristics to use and then break ties within the functions you implement
It follows similarly to the other heuristics and chekcs
'''
VariableSelectionHeuristic = {'None': 0, 'MRV': 1, 'DH': 2}
ValueSelectionHeuristic = {'None': 0, 'LCV': 1}
ConsistencyCheck = {'None': 0, 'ForwardChecking': 1, 'ArcConsistency': 2}
HeuristicCheck = {'None': 0, 'NKP': 1, 'NKT': 2, 'NKPT': 3}


class BTSolver:
    "Backtracking solver"

    ######### Constructors Method #########
    def __init__(self, gb):
        self.network = filereader.GameBoardToConstraintNetwork(gb)
        self.trail = trail.masterTrailVariable
        self.hassolution = False
        self.gameboard = gb

        self.numAssignments = 0
        self.numBacktracks = 0
        self.preprocessing_startTime = 0
        self.preprocessing_endTime = 0
        self.startTime = None
        self.endTime = None

        self.varHeuristics = 0  # refers to which variable selection heuristic in use(0 means default, 1 means MRV, 2 means DEGREE)
        self.valHeuristics = 0  # refers to which value selection heuristic in use(0 means default, 1 means LCV)
        self.cChecks = 0  # refers to which consistency check will be run(0 for backtracking, 1 for forward checking, 2 for arc consistency)
        self.heuristicChecks = 0
        # self.runCheckOnce = False
        self.tokens = []  # tokens(heuristics to use)

    ######### Modifiers Method #########


    def setTokens(self, tokens):
        ''' set the set of heuristics to be taken into consideration'''
        self.tokens = tokens

    def setVariableSelectionHeuristic(self, vsh):
        '''modify the variable selection heuristic'''
        self.varHeuristics = vsh

    def setValueSelectionHeuristic(self, vsh):
        '''modify the value selection heuristic'''
        self.valHeuristics = vsh

    def setConsistencyChecks(self, cc):
        '''modify the consistency check'''
        self.cChecks = cc

    def setHeuristicChecks(self, hc):
        '''modify the heurisic check (naked pairs and triples)'''
        self.heuristicChecks += hc

    ######### Accessors Method #########
    def getSolution(self):
        return self.gameboard

    # @return time required for the solver to attain in seconds
    def getTimeTaken(self):
        return self.endTime - self.startTime

    ######### Helper Method #########
    def checkConsistency(self):
        '''which consistency check to run but it is up to you when implementing the heuristics to break ties using the other heuristics passed in'''
        if self.cChecks == 0:
            return self.assignmentsCheck()
        elif self.cChecks == 1:
            return self.forwardChecking()
        elif self.cChecks == 2:
            return self.arcConsistency()
        else:
            return self.assignmentsCheck()

    def checkHeuristics(self):
        if self.heuristicChecks == 1:
            return self.nakedPairs()
        elif self.heuristicChecks == 2:
            return self.nakedTriples()
        elif self.heuristicChecks == 3:
            return self.nakedTriples() and self.nakedPairs()
        else:
            return True    

    def assignmentsCheck(self):
        """
            default consistency check. Ensures no two variables are assigned to the same value.
            @return true if consistent, false otherwise.
        """

        for v in self.network.variables:
            if v.isAssigned():
                for vOther in self.network.getNeighborsOfVariable(v):
                    if v.getAssignment() == vOther.getAssignment():
                        return False
        return True

    def nakedPairs(self):
        """
           TODO: Implement naked pairs heuristic.
        """
        # return -1 if fail,
        # return 0 if nk found and domain modified,
        # return 1 if nk not found
        def do_nk(v, area):
            found = False
            r_var = None
            for rv in area:
                if rv.size() == 2:
                    count = 0
                    for dom in v.Values():
                        if rv.domain.contains(dom):
                            count += 1
                    if count == 2:
                        r_var = rv
                        found = True
                        break

            if found == True:
                for rv in area:
                    if rv != r_var:
                        for dom in r_var.Values():
                            rv.removeValueFromDomain(dom)
                            if v.domain.size() == 0:
                                return False
            return True

        for v in self.network.variables:
            if v.size() == 2:
                ro = []
                co = []
                bx = []
                for nv in self.network.getNeighborsOfVariable(v):
                    if nv.row == v.row:
                        ro.append(nv)
                    if nv.col == v.col:
                        co.append(nv)
                    if nv.block == v.block:
                        bx.append(nv)
                

                if do_nk(v, ro) == False: return False
                if do_nk(v, co) == False: return False
                if do_nk(v, bx) == False: return False

        return True

    def nakedTriples(self):
        """
           TODO:  Implement naked triples heuristic.
        """
        def consistent():
            for i in self.network.variables:
                if i.isAssigned():
                    for j in self.network.getNeighborsOfVariable(i):
                        if j.isAssigned() and i.Values() == j.Values():
                            return False
            return True
        
        def remove_process(v, b_list, num):
            count = 1
            for i in b_list:
                if intersect(v.Values(), i.Values(), num):
                    count += 1
            if count == 3:
                for i in b_list:
                    if contain(v.Values(), i.Values()):
                        for j in get_inter(v.Values(), i.Values()):
                            i.removeValueFromDomain(j)
                            if i.domain.size == 0:
                                return False
        return True

        def get_inter(a, b):
           return list(set(a) & set(b))

        def intersect(a, b, num):
            inter_length = get_inter(a, b)
            if num == 3:
                return inter_length <= num and inter_length == len(b)
            if num == 2:
                return inter_length <= num and inter_length == 1
        def contain(a, b):
            inter_length = get_inter(a, b)
            return inter_length > 0 and len(b) != inter_length

        def process(v, num):
            ro = []
            co = []
            bx = []
            if v.domain.size() == num:
                for nv in self.network.getNeighborsOfVariable(v):
                    if nv.isAssigned() == False:
                        if v.row == nv.row:
                            ro.append(nv)
                        if v.col == nv.col:
                            co.append(nv)
                        if v.block == nv.block:
                            bx.append(nv)
                if remove_process(v, ro, num) == False: return False
                if remove_process(v, co, num) == False: return False
                if remove_process(v, bx, num) == False: return False  
            
        for v in self.network.variables:
            process(v, 2)
            process(v, 3)
                    
        return consistent()

    def forwardChecking(self):
        """
           TODO:  Implement forward checking.
        """
        def consistent():
            for i in self.network.variables:
                if i.isAssigned():
                    for j in self.network.getNeighborsOfVariable(i):
                        if j.isAssigned() and i.Values() == j.Values():
                            return False
            return True
    
        for i in self.network.variables:
            if i.isAssigned():
                for j in self.network.getNeighborsOfVariable(i):
                    if j.isAssigned() == False:
                        j.removeValueFromDomain(i.Values()[0])
                        if j.domain.size() == 0:
                            return False
        return consistent()

    def arcConsistency(self):
        """
            TODO: Implement Maintaining Arc Consistency.
        """
        queue = []
        for v in self.network.variables:
            queue = self.network.getConstraintsContainingVariable(v)
            while len(queue) > 0:
                arcs = queue.pop()
                if arcs.propagateConstraint() == False:
                    return False

        return True

    def selectNextVariable(self):
        """
            Selects the next variable to check.
            @return next variable to check. null if there are no more variables to check.
        """
        if self.varHeuristics == 0:
            return self.getfirstUnassignedVariable()
        elif self.varHeuristics == 1:
            return self.getMRV()
        elif self.varHeuristics == 2:
            return self.getDegree()
        else:
            return self.getfirstUnassignedVariable()

    def getfirstUnassignedVariable(self):
        """
            default next variable selection heuristic. Selects the first unassigned variable.
            @return first unassigned variable. null if no variables are unassigned.
        """
        for v in self.network.variables:
            if not v.isAssigned():
                return v
        return None

    def getMRV(self):
        """
            TODO: Implement MRV heuristic
            @return variable with minimum remaining values that isn't assigned, null if all variables are assigned.
        """
        dom_sz = 9999
        var = None
        for v in self.network.variables:
            if v.isAssigned() == False:
                sz = v.domain.size()
                if dom_sz > sz:
                    dom_sz = sz
                    var = v

        return var
        

    def getDegree(self):
        """
            TODO: Implement Degree heuristic
            @return variable constrained by the most unassigned variables, null if all variables are assigned.
        """
        maxd = -1
        var = None
        for v in self.network.variables:
            if v.isAssigned() == False:
                degree = 0
                for nv in self.network.getNeighborsOfVariable(v):
                    if nv.isAssigned() == False:
                        degree += 1

                if degree > maxd:
                    maxd = degree
                    var = v

        return var
      

    def getNextValues(self, v):
        """
            Value Selection Heuristics. Orders the values in the domain of the variable
            passed as a parameter and returns them as a list.
            @return List of values in the domain of a variable in a specified order.
        """
        if self.valHeuristics == 0:
            return self.getValuesInOrder(v)
        elif self.valHeuristics == 1:
            return self.getValuesLCVOrder(v)
        else:
            return self.getValuesInOrder(v)


    def getValuesInOrder(self, v):
        """
            Default value ordering.
            @param v Variable whose values need to be ordered
            @return values ordered by lowest to highest.
        """
        values = v.domain.values
        return sorted(values)


    def getValuesLCVOrder(self, v):
        """
            TODO: LCV heuristic
        """
        sorted_dom = []
        if v.isAssigned() == False:
            for dom in v.Values():
                count = 0
                for nv in self.network.getNeighborsOfVariable(v):
                    if nv.domain.contains(dom):
                        count += 1
                sorted_dom.append((dom, count))

        sorted_dom = sorted(sorted_dom, key=lambda num: sorted_dom[1])
        only_dom = [dm for dm, ct in sorted_dom]
                
        return only_dom


    def success(self):
        """ Called when solver finds a solution """
        self.hassolution = True
        self.gameboard = filereader.ConstraintNetworkToGameBoard(self.network,
                                                                 self.gameboard.N,
                                                                 self.gameboard.p,
                                                                 self.gameboard.q)


    ######### Solver Method #########
    def solve(self):
        """ Method to start the solver """
        self.startTime = time.time()
        # try:
        self.solveLevel(0)
        # except:
        # print("Error with variable selection heuristic.")
        self.endTime = time.time()
        # trail.masterTrailVariable.trailStack = []
        self.trail.trailStack = []


    def solveLevel(self, level):
        """
            Solver Level
            @param level How deep the solver is in its recursion.
            @throws VariableSelectionException
        contains some comments that can be uncommented for more in depth analysis
        """
        # print("=.=.=.=.=.=.=.=.=.=.=.=.=.=.=.=")
        # print("BEFORE ANY SOLVE LEVEL START")
        # print(self.network)
        # print("=.=.=.=.=.=.=.=.=.=.=.=.=.=.=.=")

        if self.hassolution:
            return

        # Select unassigned variable
        v = self.selectNextVariable()
        # print("V SELECTED --> " + str(v))

        # check if the assigment is complete
        if (v == None):
            # print("!!! GETTING IN V == NONE !!!")
            for var in self.network.variables:
                if not var.isAssigned():
                    raise ValueError("Something happened with the variable selection heuristic")
            self.success()
            return

        # loop through the values of the variable being checked LCV
        # print("getNextValues(v): " + str(self.getNextValues(v)))
        for i in self.getNextValues(v):
            # print("next value to test --> " + str(i))
            self.trail.placeTrailMarker()

            # check a value
            # print("-->CALL v.updateDomain(domain.Domain(i)) to start to test next value.")
            v.updateDomain(domain.Domain(i))
            self.numAssignments += 1

            # move to the next assignment
            if self.checkConsistency() and self.checkHeuristics():
                self.solveLevel(level + 1)

            # if this assignment failed at any stage, backtrack
            if not self.hassolution:
                # print("=======================================")
                # print("AFTER PROCESSED:")
                # print(self.network)
                # print("================ ")
                # print("self.trail before revert change: ")
                for i in self.trail.trailStack:
                    pass
                    # print("variable --> " + str(i[0]))
                    # print("domain backup --> " + str(i[1]))
                # print("================= ")

                self.trail.undo()
                self.numBacktracks += 1
                # print("REVERT CHANGES:")
                # print(self.network)
                # print("================ ")
                # print("self.trail after revert change: ")
                for i in self.trail.trailStack:
                    pass
                    # print("variable --> " + str(i[0]))
                    # print("domain backup --> " + str(i[1]))
                # print("================= ")

            else:
                return
