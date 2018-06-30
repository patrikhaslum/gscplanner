
/[0-9]\+\. /! d

s/^[0-9]\+\. /(/
s/_block_/ b/g
s/_cylinder_/ c/g
s/_from//
s/_onto//
s/_in//
s/ (1)/)/
