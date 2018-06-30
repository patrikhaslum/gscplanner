
(define (domain AC_PSR)
  (:requirements :strips :typing :fluents :action-costs)

  (:types bus branch)

  (:predicates
   (faulty ?b - bus)
   (closed ?b - branch)
   (open ?b - branch)
   (ends ?b - branch ?b1 - bus ?b2 - bus)
   )

  (:functions
   (status)
   (fed ?b - bus)
   (unsafe ?b - bus)
   (switch_state ?b - branch)
   (total-cost)
   )

  (:action open
   :parameters (?br - branch ?b1 - bus ?b2 - bus)
   :precondition (and (ends ?br ?b1 ?b2)
		      (closed ?br)
		      (>= (status) 1))
   :effect (and (not (closed ?br))
		(open ?br)
		(assign (switch_state ?br) 0)
		(assign (unsafe ?b1) 0)  ; heuristic effect
		(assign (unsafe ?b2) 0)  ; heuristic effect
		(increase (total-cost) 1))
   )

  (:action close
   :parameters (?br - branch ?b1 - bus ?b2 - bus)
   :precondition (and (ends ?br ?b1 ?b2)
		      (open ?br)
		      (<= (+ (fed ?b1) (unsafe ?b2)) 1)
		      (<= (+ (fed ?b2) (unsafe ?b1)) 1)
		      (>= (status) 1))
   :effect (and (not (open ?br))
		(closed ?br)
		(assign (switch_state ?br) 1)
		(increase (fed ?b1) (fed ?b2))  ; heuristic effect
		(increase (fed ?b2) (fed ?b1))  ; heuristic effect
		(increase (total-cost) 1))
   )

  )
