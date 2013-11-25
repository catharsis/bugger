def distance(s1, s2):
	'''
	>>> distance("cheese", "cheeso")
	1
	>>> distance("kitten", "sitting")
	3
	>>> distance("coffee", "coffee")
	0
	>>> distance("foo", "bar")
	3
	>>> distance("robot", "robotnik")
	3
	'''
	if len(s1) == 0: return len(s2)
	if len(s2) == 0: return len(s1)

	if s1[-1] == s2[-1]:
		cost = 0
	else:
		cost = 1

	return min( distance(s1[:-1], s2) + 1,
			distance(s1, s2[:-1]) + 1,
			distance(s1[:-1], s2[:-1]) + cost
			)
