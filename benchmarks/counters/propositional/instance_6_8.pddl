
(define (problem instance-6-8)
  (:domain counters-propositional)

  (:objects
   c0 c1 c2 c3 c4 c5 - counter
   i0 i1 i2 i3 i4 i5 i6 i7 - integer
   )

  (:init
   ;; +1
   (next i0 i1)
   (next i1 i2)
   (next i2 i3)
   (next i3 i4)
   (next i4 i5)
   (next i5 i6)
   (next i6 i7)
   (next i7 i8)

   ;; less than
   (less i0 i1)
   (less i0 i2)
   (less i0 i3)
   (less i0 i4)
   (less i0 i5)
   (less i0 i6)
   (less i0 i7)

   (less i1 i2)
   (less i1 i3)
   (less i1 i4)
   (less i1 i5)
   (less i1 i6)
   (less i1 i7)

   (less i2 i3)
   (less i2 i4)
   (less i2 i5)
   (less i2 i6)
   (less i2 i7)

   (less i3 i4)
   (less i3 i5)
   (less i3 i6)
   (less i3 i7)

   (less i4 i5)
   (less i4 i6)
   (less i4 i7)

   (less i5 i6)
   (less i5 i7)

   (less i6 i7)

   ;; initial values
   (value c0 i0)
   (value c1 i0)
   (value c2 i0)
   (value c3 i0)
   (value c4 i0)
   (value c5 i0)

   ;; initially in plan mode
   (plan)
   (= (total-cost) 0)
   )

  (:goal (and (ok c0 c1)
	      (ok c1 c2)
	      (ok c2 c3)
	      (ok c3 c4)
	      (ok c4 c5)
	      ))

  (:metric minimize (total-cost))
  )
