(define (domain hydraulic_blocks_world)
  (:requirements :typing)

  (:types block cylinder)

  (:constants c0 c1 c2 - cylinder)
  
  (:predicates
   (on ?b_above - block ?b_below - block)
   (on_piston ?b - block)
   (clear_piston ?c - cylinder)
   (clear ?b - block)
   (in ?b - block ?c - cylinder)
   (holding ?b - block)
   (handempty)
   )
  
  (:functions
   (weight_on ?c - cylinder)
   ;; everything else is static
   ;; problem parameters:
   (weight ?b - block)
   (area ?c - cylinder)
   (height ?c - cylinder)
   (volume)
   (density)
   ;; total_area = sum of all cylinder areas
   (total_area)
   )

  ;; h1 = (+ (/ (volume) (total_area))
  ;;         (/ (weight_on c2) (total_area))
  ;;         (/ (weight_on c3) (total_area))
  ;;         (* -1 (/ (+ (area c2) (area c3)) (* (total_area) (area c1))) (weight_on c1)))

  (:constraint lb_c0
   :parameters ()
   :condition (>= (+ (* (/ 1 (total_area)) (volume))
  		     (+ (* (/ 1 (total_area)) (/ (weight_on c1) (density)))
  			(- (* (/ 1 (total_area)) (/ (weight_on c2) (density)))
			   (* (/ (- (total_area) (area c0))
				 (* (total_area) (area c0)))
			      (/ (weight_on c0) (density))))))
  		  0)
   )

  (:constraint ub_c0
   :parameters ()
   :condition (<= (+ (* (/ 1 (total_area)) (volume))
  		     (+ (* (/ 1 (total_area)) (/ (weight_on c1) (density)))
  			(- (* (/ 1 (total_area)) (/ (weight_on c2) (density)))
			   (* (/ (- (total_area) (area c0))
				 (* (total_area) (area c0)))
			      (/ (weight_on c0) (density))))))
  		  (height c0))
   )

  (:constraint lb_c1
   :parameters ()
   :condition (>= (+ (* (/ 1 (total_area)) (volume))
  		     (+ (* (/ 1 (total_area)) (/ (weight_on c0) (density)))
  			(- (* (/ 1 (total_area)) (/ (weight_on c2) (density)))
			   (* (/ (- (total_area) (area c1))
				 (* (total_area) (area c1)))
			      (/ (weight_on c1) (density))))))
  		  0)
   )

  (:constraint ub_c1
   :parameters ()
   :condition (<= (+ (* (/ 1 (total_area)) (volume))
  		     (+ (* (/ 1 (total_area)) (/ (weight_on c0) (density)))
  			(- (* (/ 1 (total_area)) (/ (weight_on c2) (density)))
			   (* (/ (- (total_area) (area c1))
				 (* (total_area) (area c1)))
			      (/ (weight_on c1) (density))))))
  		  (height c1))
   )

  (:constraint lb_c2
   :parameters ()
   :condition (>= (+ (* (/ 1 (total_area)) (volume))
  		     (+ (* (/ 1 (total_area)) (/ (weight_on c0) (density)))
  			(- (* (/ 1 (total_area)) (/ (weight_on c1) (density)))
			   (* (/ (- (total_area) (area c2))
				 (* (total_area) (area c2)))
			      (/ (weight_on c2) (density))))))
  		  0)
   )

  (:constraint ub_c2
   :parameters ()
   :condition (<= (+ (* (/ 1 (total_area)) (volume))
  		     (+ (* (/ 1 (total_area)) (/ (weight_on c0) (density)))
  			(- (* (/ 1 (total_area)) (/ (weight_on c1) (density)))
			   (* (/ (- (total_area) (area c2))
				 (* (total_area) (area c2)))
			      (/ (weight_on c2) (density))))))
  		  (height c2))
   )


  ;; unstack ?a from ?b in cylinder ?c
  (:action unstack
   :parameters (?a ?b - block ?c - cylinder)
   :precondition (and (on ?a ?b)
		      (clear ?a)
		      (handempty)
		      (in ?a ?c))
   :effect (and (not (on ?a ?b))
		(not (clear ?a))
		(not (handempty))
		(holding ?a)
		(clear ?b)
		(not (in ?a ?c))
		(decrease (weight_on ?c) (weight ?a)))
   )

  ;; stack ?a on ?b in cylinder ?c
  (:action stack
   :parameters (?a ?b - block ?c - cylinder)
   :precondition (and (holding ?a)
		      (clear ?b)
		      (in ?b ?c))
   :effect (and (not (holding ?a))
		(not (clear ?b))
		(on ?a ?b)
		(clear ?a)
		(handempty)
		(in ?a ?c)
		(increase (weight_on ?c) (weight ?a)))
   )

  ;; pickup ?a from piston in cylinder ?c
  (:action pickup
   :parameters (?a - block ?c - cylinder)
   :precondition (and (on_piston ?a)
		      (clear ?a)
		      (handempty)
		      (in ?a ?c))
   :effect (and (not (on_piston ?a))
		(not (clear ?a))
		(not (handempty))
		(holding ?a)
		(clear_piston ?c)
		(not (in ?a ?c))
		(decrease (weight_on ?c) (weight ?a)))
   )

  ;; put ?a down on piston in cylinder ?c
  (:action putdown
   :parameters (?a - block ?c - cylinder)
   :precondition (and (holding ?a)
		      (clear_piston ?c))
   :effect (and (not (holding ?a))
		(not (clear_piston ?c))
		(on_piston ?a)
		(clear ?a)
		(handempty)
		(in ?a ?c)
		(increase (weight_on ?c) (weight ?a)))
   )

  )
