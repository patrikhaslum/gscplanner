from model.planning import *

#builds a relaxed planning graph and does the iterative landmark generation

#--------------------------------------------

#Relaxed planning graph

#--------------------------------------------

#layer consists of a ustate and a list of actions that could be applied
class R_p_layer:
    def __init__(self,ustate,applied_actions,available_actions):
        self.ustate=ustate                  #assignments for the primary variables
        self.available_actions=available_actions   #unapplied actions
        self.applied_actions=applied_actions #actions applied in the previous state to reach this state
    def pstring(self):
        s="\nActions applied to reach the state:\n"
        s=s+pstring_actions(self.applied_actions)
        s=s+"\nValues over the variables:\n"
        s=s+self.ustate.pstring()
        s=s+"\nRemaining actions:\n"
        s=s+pstring_actions(self.available_actions)
        return s

class R_p_graph:
    def __init__(self,problem):
        self.problem=problem                  #assignments for the primary variables
#        self.all_actions=problem.p_action #NOTE: Used by add action... unsure whether needed? 
        self.actions=problem.p_action   #unapplied actions
        self.layers=[] #a list of states, initally empty
    def astart(self):
        return (self.problem).p_start
    def constraints(self):
        return (self.problem).p_invar
    def goal(self):
        return (self.problem).p_goal
    def pvars(self):
        return (self.problem).p_vars_p
    def tmodel(self):
        return (self.problem).transition_model
    def gmodel(self):
        return (self.problem).goal_model
    def svars(self):
        return (self.problem).p_vars_s
    def constraints_to_check(self):
        return (self.problem).constraints_to_check
    def goal_reached(self):
#        print "Calling goal reached..."
        g=self.goal()
        if len(self.layers)<1:
          return False
        last_layer=self.layers[-1]
        last_ustate=last_layer.ustate
        return g.u_reached(last_ustate,self.gmodel(),constraints=self.constraints_to_check())
    def add_action_to_end_layer(self,action):
        final_layer=self.layers[-1]
        final_layer.available_actions.append(action)
    def add_start_layer(self):
        start_ustate=(self.astart()).make_pustate()
        start_actions=self.actions
        (self.layers).append(R_p_layer(start_ustate,[],start_actions))
    def add_next_layer(self): #returns True if the new layer is different from the old one (at least one action was applied)
        if(len(self.layers)<1):
          number_of_actions=self.add_start_layer()
          return True
        else:
          from_layer=self.layers[-1]
          available_actions=from_layer.available_actions
          current_ustate=from_layer.ustate
          
          #This line is used forn non-relaxed version. It checks whether the resulting ustate is allowed 
          #NOTE Uncomment out to return to the tighter relaxation.
          #[new_state,unapplied_a,applied_a]=u_apply_return_unapplied_actions(available_actions,current_ustate,self.tmodel(),self.constraints_to_check())

          #This function assumes that the resulting ustate is allowed 
          #NOTE Comment out to return to the tighter relaxation.
          [new_state,unapplied_a,applied_a]=u_apply_return_unapplied_actions_relaxed(available_actions,current_ustate,self.tmodel(), self.constraints_to_check())
          
          if len(applied_a)>0:
            new_layer=R_p_layer(new_state,applied_a,unapplied_a)
            self.layers.append(new_layer)
            return True #if actions were applied in making the layer returns True
        return False #
    def no_actions_applicable(self):
        if len(self.layers)<2:
          return False
        current_state=self.layers[-1]
        if len(current_state.applied_actions)<1:
          return True
        return False
    def build_graph(self): #given a problem, builds a graph until the goal is reached
        g=self.goal_reached()
        new_layer_added=True
        i=0
        while(not(g) and new_layer_added):
          new_layer_added=self.add_next_layer()
          g=self.goal_reached()        
        return g
    def pstring(self): #prints out the graph
        s=""
        i=0
        for l in self.layers:
          s=s+"\n----------------------------State {0}----------------------------\n".format(i)
          s=s+l.pstring()          
          i=i+1
        return s
    def reset_layers(self):
        self.layers=[]
        self.actions=(self.problem).p_action
        
        #similar to the check_reachability, except doesn't keep the action in the unapplied actions
    def try_action(self,action):
         
        current_layer=self.layers[-1]
        [new_state,unapplied_a,applied_a]=u_apply_return_unapplied_actions_relaxed([action],current_layer.ustate,self.tmodel(), self.constraints_to_check())
        if len(applied_a)>0: #if the action was successfully applied
          new_layer=R_p_layer(new_state,applied_a,[]) #create a new layer
          self.layers.append(new_layer) #append it to the graph
          return True
        return False

   
    #old functions
    """
    def printstate(self):
        print('\nPrimary variables:')
        for i in self.pvars():
            i.uprint()
        g=self.goal()
        print('\nIs the goal reached? {0}\n'.format(self.goal_reached()))
        print('Remaining actions:')
        for i in self.actions:
            print(i.name)
        print("")
    def apply_actions_print(self): 
        print("")
        if(len(self.actions)==0):
            print("No actions left")
        allowed_actions=set()
        print("Allowed actions:")
        for a in self.actions:
            print("Checking whether {0} allowed".format(a.name))
            if(a.u_allowed(self.constraints(),self.svars())):
                print("Allowed {0}".format(a.name))
                allowed_actions.add(a)
        applied_actions=set()
        for a in allowed_actions:
            if(u_apply(a, self.constraints(),self.svars())): 
                print('Action {0} applied'.format(a.name))
                applied_actions.add(a)
        self.actions=(self.actions).difference(applied_actions)
        print("")
        return len(allowed_actions)>0

    def build_graph_print(self): #builds and prints the whole graph. Returns whether goal reached
        print("\n---------------Start state-----------------")
        self.printstate() #print the initial
        allowed_actions_remaining=len(self.actions)>0
#        print("{0} {1}".format(not(self.goal_reached()),actions_remaining))
        i=1
        while(not(self.goal_reached()) and allowed_actions_remaining):
            print("---------------Actions {0}------------------".format(i))
            allowed_actions_remaining=self.apply_actions_print()
            print("---------------Union state {0}---------------".format(i))
            self.printstate()
#            actions_remaining=len(self.actions)>0
            i=i+1
        return self.goal_reached()
    def apply_actions(self):
        allowed_actions=set()
        for a in self.actions:
            if(a.u_allowed(self.constraints(),self.svars())):
                allowed_actions.add(a)
        applied_actions=set()
        for a in allowed_actions:
            if(u_apply(a, self.constraints(),self.svars())): 
                applied_actions.add(a)
        self.actions=(self.actions).difference(applied_actions)
        return len(allowed_actions)>0
  """

#cheks whether an action can be applied to the last state. If yes, it also cheks whether any other other unapplied actions are now now applicable.
#How it actually works - it adds an action to the graph.actions. If the function is applicable, it builds a graph and returns 
def check_reachability_addAction_end(graph,action):
  graph.actions.append(action)
  current_layer=graph.layers[-1]
  if pvalu_ucheck(action.a_effpv,current_layer.ustate): #can this action make any difference? If the effects of the action are already valid
    return False #return False
  
  #This line is used forn non-relaxed version. It checks whether the resulting ustate is allowed 
  #NOTE Uncomment out to return to the tighter relaxation.
  #[new_state,unapplied_a,applied_a]=u_apply_return_unapplied_actions([action],current_layer.ustate,graph.tmodel(),graph.constraints_to_check())
  
  #This function assumes that the resulting ustate is allowed. 
  #NOTE Comment out to return to the tighter relaxation.
  [new_state,unapplied_a,applied_a]=u_apply_return_unapplied_actions_relaxed([action],current_layer.ustate,graph.tmodel(),graph.constraints_to_check())
  
  if len(applied_a)>0: #if the action was successfully applied
    new_layer=R_p_layer(new_state,applied_a,current_layer.available_actions) #create a new layer
    graph.layers.append(new_layer) #append it to the graph
    if graph.goal_reached(): #if the goal is reached, return True
      return True 
    else: #if not, build graph and see whether the goal can now be reached with any of the other actions
      return graph.build_graph()
  else: #if the action could not be applied, add it to the final layer
    graph.add_action_to_end_layer(action)
  return False 

#similar as above, except for a set of actions
def check_reachability_using_set(graph,actions):
    graph.actions=actions
    goal_reachable=graph.build_graph()
    return goal_reachable



#similar to above, except it searches for the earliest place to apply an action
#check reachability without reseting - just adds one action to the graph
#the way this function works is - given a graph, it finds the earliest union state in which the action can be applied. All the subsequant 
#union states are modified accordingly.
#NOTE: Not done (but not used either)
def check_reachability_addAction_early(graph,action):
    
    #check whether the action can be applied in any of the layers
    for l in graph.layers:
      pass
    
    print("Adding action {0}".format(action.name))
    
    if(action.u_allowed(graph.constraints(),graph.svars())): #if action is allowed
        u_apply(action, graph.constraints(),graph.svars()) #apply the action
        allowed_actions=[]
        for a in graph.actions: #check whether the application of this action makes any actions before applicable
            if(a.u_allowed(graph.constraints(),graph.svars())):
                allowed_actions.append(a)
        applied_actions=set()
        for a in allowed_actions: #apply the allowed actions
            if(u_apply(a, graph.constraints(),graph.svars())): 
                applied_actions.add(a)
        graph.actions=(graph.actions).difference(applied_actions)
        return graph.goal_reached() #return whether the goal has been reached
    else: #else the action is added to the unapplied actions set
        graph.actions.add(action)
    return False
     




#--------------------------------------------

#Iterative landmark

#--------------------------------------------

#rewriting the iterative landmark function
def iterative_landmark(problem,collectionL=[]):
    
  #  collectionL=[] #collection of sets
    setA=set() #minimum cost hitting set of L
    graph=R_p_graph(problem)
    
 #   print "Checking reachability with an empty set"
    goal_reachable=check_reachability_using_set(graph,list(setA)) #chacking whether the goal can be reached with an empty set (whether the goal is achieved in the start state)
  #  print goal_reachable
    
    for l in collectionL:
      for a in l:
        if a not in problem.p_action:
          print "Action not in problem!!"
          raise Error
    
    i=0 #counter for debugging   
    while not(goal_reachable):# and i<10): 
        
#        print "going into while loop... {0}".format(i)
        
        collectionL.append(new_landmark(graph,setA)) #use setA to add a new landmark 
#        print pstring_action_collection(collectionL)
        setA=min_cost_hitting_set(collectionL,problem.p_action)         #create new setA
        graph.reset_layers()                                         #reset the graph
        goal_reachable=check_reachability_using_set(graph,list(setA)) #check whether the new setA reaches the goal
        
#        print "What are the graph.actions?"
#        print_set_elements(graph.actions)
#        print "SetA?"
#        print_set_elements(setA)
        i=i+1 #counter for debugging
        
    graph.reset_layers()
    return [collectionL,setA]



#new landmark
def new_landmark(graph, setA):
  
#  print("new landmark...")

  #set up the sets and lists
  problem_actions=set(graph.problem.p_action)
  complement_setA=problem_actions.difference(setA) #should be empty only if setA contains all actions.
  c_setA_list=list(complement_setA)
  
  #NOTE: assumption here is that the goal is NOT reachable with setA
  
  #check each action
  for c_action in c_setA_list:
    
    #NOTE: There shouldbe a bunch of stuff here instead of the addAction function
      length_of_the_graph_before=len(graph.layers)
 #     current_pvstate=graph.problem.current_pvstate() #saves a state before applying the action    #NOTE: Not used anymore
      if not(check_reachability_addAction_end(graph,c_action)): #NOTE: Mistake here, I think         #Fixed, I think    
#          print("Adding {0}".format(c_action.name))
          setA.add(c_action)
      else:
#          current_pvstate.getstate() #NOTE: Not used anymore... instead, it deletes the last layer from the graph.
          graph.layers=graph.layers[:length_of_the_graph_before]
#          print("Not adding {0}".format(c_action.name))

  complement_setA=problem_actions.difference(setA)
  
#  print "\n\n\n\n\n\n\n\n"
 # print "SetA:"
  #print pstring_names_set_elements(setA)
#  print "Problem actions:"
 # print pstring_names_set_elements(problem_actions)
  #print "Returning:"
#  print pstring_names_set_elements(complement_setA)  
 # print "\n\n\n\n\n\n\n\n"
  
  return complement_setA


#minimum cost hitting set. Uses Gurobi
def min_cost_hitting_set(L,actions):
  
  #the model
  m=Model("min_cost_hitting_set")
  m.setParam("OutputFlag",0) #suppresing the output

  #adding the variables and making the objective expression 
  obj_expr=0
  for a in actions:
    #print a.name,a.cost
    #print "The action is: ",a
    #print "The variable is", a.var
    a.var=m.addVar(vtype=GRB.BINARY)
    m.update()
    #print "The variable is", a.var
    obj_expr=obj_expr+a.cost*a.var
    
  
  #objective function - total cost of the hitting set
  m.update()
  m.setObjective(obj_expr, GRB.MINIMIZE)
  m.update()
#  print "The objective expression is: ",obj_expr
 # print "Length of L is",len(L)
  #print pstring_action_collection(L)
  #the constraints - for each landmark, the cost of functions in a must be at least 1
  for landmark in L:
    landmark_constr_expr=0
    for a in landmark:
     # print "Adding:",a.name
      #print "Is the action in problem actions? ", a in actions 
      #print "The action is: ",a
      #print "The variable is", a.var
      m.update()
      #print "The variable is", a.var
      landmark_constr_expr=landmark_constr_expr+a.var
      #print "Landmark constr expression is:",landmark_constr_expr
    m.addConstr(landmark_constr_expr,GRB.GREATER_EQUAL,1)
    
  #solve
  m.update()
  m.optimize()
  
  """
  for a in actions:
    print a.name
    print a.var
    print a.var.x
 """
  
  #read out the solution
  setA=set() #read the solution
  for a in actions: #go through the actions and see which are used
   # print a.var
    if a.var.x:
      setA.add(a)
  
  return setA


#remove landmarks containing action
def remove_landmarks_containing_action(collectionL,action):
  newL=[]
  for l in collectionL:
    if not(action in l):
      newL.append(l)
  return newL


#function which sums the costs of the actions in a set
def sum_action_costs(action_set):
  cost=0
  for action in action_set:
    cost=cost+action.cost
  return cost

#functions for testing
#print the set elements (generally usefulfor anything that has a "name")
def pstring_names_set_elements(action_set):
  s="Set:\n"
  for i in action_set:
    s=s+i.name+"\n"
  return s

#prints out elements of each set in a collection
def pstring_action_collection(collectionL):
  s="Collection:\n\n"
  for i in collectionL:
    s=s+pstring_names_set_elements(i)+"\n"
  return s

