
/^(0.00000 )Action Name:/! d

s/(0\.00000 )Action Name:pickup Parameters: b\([0-9]\)  - block  c\([0-9]\)  - cylinder  /pickup_block_\1_from_cylinder_\2/
s/(0.00000 )Action Name:putdown Parameters: b\([0-9]\)  - block  c\([0-9]\)  - cylinder  /putdown_block_\1_onto_cylinder_\2/
s/(0.00000 )Action Name:unstack Parameters: b\([0-9]\)  - block  b\([0-9]\)  - block  c\([0-9]\)  - cylinder  /unstack_block_\1_from_block_\2_in_cylinder_\3/
s/(0.00000 )Action Name:stack Parameters: b\([0-9]\)  - block  b\([0-9]\)  - block  c\([0-9]\)  - cylinder  /stack_block_\1_onto_block_\2_in_cylinder_\3/
