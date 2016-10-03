#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2016-10-03 17:37:11
# @Version : $python 2.7.11

from itertools import chain, combinations

# A class to encapsulate a Functional Dependency, and some helper functions
class FD:
	def __init__(self, lhs, rhs):
		self.lhs = frozenset(list(lhs))
		self.rhs = frozenset(list(rhs))
	def __str__(self):
		return ''.join(self.lhs) + " -> " + ''.join(self.rhs)
	def __eq__(self, other):
		return (self.lhs == other.lhs) & (self.rhs == other.rhs)
	def __hash__(self):
		return hash(self.lhs) * hash(self.rhs)
	def isTrivial(self):
		"""A functional dependency is trivial if the right hand side is a subset of the left h.s."""
		return self.lhs >= self.rhs

# The following is not really needed for normalization, but may be useful to get intuitions about FDs
class Relation: 
	def __init__(self, schema):
		self.tuples = list()
		self.schema = schema 
	def add(self, t):
		if len(t) == len(self.schema):
			self.tuples.append(t)
		else:
			print "Added tuple does not match the length of the schema"
	def checkIfMatch(self, t1, t2, attr_set):
		return all(t1[self.schema.index(attr)] == t2[self.schema.index(attr)] for attr in attr_set)
	def checkFDHolds(self, fd): 
		"""Go over all pairs of tuples and see if the FD is violated"""
		for t1 in self.tuples:
			for t2 in self.tuples:
				if t1 < t2 and self.checkIfMatch(t1, t2, fd.lhs) and not self.checkIfMatch(t1, t2, fd.rhs):
					print "Tuples " + str(t1) + " and " + str(t2) + " violate the FD " + str(fd)

r = Relation(['A', 'B', 'C'])
r.add([1, 2, 3])
r.add([2, 2, 3])
r.checkFDHolds(FD('ABC', 'A'))

def breakdown(ls):
	F = set()
	for i in ls:
		lhs = ''.join(str(e) for e in i[0])
		rhs = ''.join(str(e) for e in i[1])
		F.add(FD(lhs,rhs))
	return F

def SingularBD(ls):
	lhs = ''.join(str(e) for e in ls[0])
	rhs = ''.join(str(e) for e in ls[1])
	return FD(lhs,rhs)

def powerset(S):
	"""Returns the powerset of a set, except for the empty set, i.e., if S = {A, B, C}, returns {{A}, {B}, {C}, {A,B}, {B,C}, {A,C}, {A,B,C}"""
	return list(chain.from_iterable(combinations(S, r) for r in range(1, len(S)+1)))

def applyreflexivity(R): 
	"""Generates all trivial dependencies, i.e., of the type X -> subset(X)"""
	return { FD(i, j) for i in powerset(R) for j in powerset(i) }

def applyaugmentation(F, PW, printflag):
	"""Augmentation: if X --> Y, then XZ --> YZ
	PW is powerset of the schema
	"""
	N = {FD(x.lhs.union(y), x.rhs.union(y)) for x in F for y in PW}
	for fd in N - F:
		if printflag: print "	Adding " + str(fd) + " by Augmenting " + str(x) + " using " + "".join(y)
	return F.union(N)

def applytransitivity(F, printflag):
	"""Transitivity: if X --> Y, and Y --> Z, then X --> Z"""
	N = { FD(x.lhs, y.rhs)	for x in F for y in F if x.rhs == y.lhs }
	for fd in N - F:
		if printflag: 
			print "	Adding " + str(fd) + " using Transitivity from " + str(x) + " and " + str(y)
	return F.union(N)

# Pesudo Output which gives string format of FDs
def closure(R, F, printflag = False):
	"""Finds closure by repeatedly applying the three Armstrong Axioms, until there is no change"""
	# Coversion
	try:
		F = breakdown(F)
	except:
		F = SingularBD(F)
	# Start with adding all trivial dependencies generated by using Reflexivity
	F = F.union(applyreflexivity(R))
	powersetR = list(chain.from_iterable(combinations(list(R), r) for r in range(1, len(R)+1)))
	Fset = []
	# Repeat application of the other two rules until no change
	done = False;
	while done == False:
		if printflag: print "Trying to find new FDs using Transitivity"
		F2 = applytransitivity(F, printflag)
		if printflag: print "Trying to find new FDs using Augmentation"
		F2 = applyaugmentation(F2, powerset(R), printflag)
		done = len(F2) == len(F)
		F = F2
	if printflag: print "Finished"
	for i in F:
		Fset.append(str(i))
	return Fset

# The real Closure Function
def Rclosure(R, F, printflag = False): 
	"""Finds closure by repeatedly applying the three Armstrong Axioms, until there is no change"""
	# Input Coversion
	try:
		F = breakdown(F)
	except:
		F = SingularBD(F)
	# Start with adding all trivial dependencies generated by using Reflexivity
	F = F.union(applyreflexivity(R))
	powersetR = list(chain.from_iterable(combinations(list(R), r) for r in range(1, len(R)+1)))
	# Fset = []
	# Repeat application of the other two rules until no change
	done = False;
	while done == False:
		if printflag: print "Trying to find new FDs using Transitivity"
		F2 = applytransitivity(F, printflag)
		if printflag: print "Trying to find new FDs using Augmentation"
		F2 = applyaugmentation(F2, powerset(R), printflag)
		done = len(F2) == len(F)
		F = F2
	if printflag: print "Finished"
	# for i in F:
	# 	Fset.append(i)
	return F

def findKeys(R, FClosure):
	"""Keys are those where there is an FD with rhs = R"""
	return { fd.lhs for fd in FClosure if len(fd.rhs) == len(list(R)) }

def findCandidateKeys(R, FClosure):
	"""Candidate keys are minimal -- go over the keys increasing order by size, and add if no subset is present"""
	keys = findKeys(R, FClosure)
	ckeys = set()
	for k in sorted(keys, lambda x, y: cmp(len(x), len(y))):
		dontadd = False
		for ck in ckeys:
			if(ck <= k):
				dontadd = True  #Found a subset already in ckeys
		if not dontadd: 
			ckeys.add(k)
	return ckeys

def isInBCNF(R, FClosure, keys):
	"""Find if there is a FD alpha --> beta s.t. alpha is not a key"""
	if keys is None: keys = Keys(R, FClosure)
	for fd in FClosure:
		if (not fd.isTrivial()) and (fd.lhs not in keys):
			return False
	return True

def listAllBCNFViolations(R, FClosure, keys):
	"""Same as above, but finds all violations and prints them"""
	for fd in FClosure:
		if (not fd.isTrivial()) and (fd.lhs not in keys):
			print str(fd) + " is an FD whose LHS is not a key"

def findSmallestViolatingFD(R, FClosure, keys):
	"""Same as above, but finds a small FD that violates"""
	for fd in sorted(FClosure, lambda x, y: cmp(len(x.lhs), len(y.lhs))):
		if (not fd.isTrivial()) and (fd.lhs not in keys):
			return fd

def DecomposeUsingFD(R, FClosure, fd):
	"""Uses the given FD to decompose the schema -- returns the resulting schemas and their closures
	Let the fd be X --> Y
	Then we create two relations: R1 = X UNION Y, and R2 = X UNION (R - Y)
	Then, for R1, we find all FDs from FClosure that apply to R1 (i.e., that only contain attributes from R1)
	And do the same for R2
	"""
	R1 = fd.lhs | fd.rhs
	R2 = set(R) - R1 | fd.lhs
	F1Closure = { fd for fd in FClosure if (fd.lhs <= R1) and (fd.rhs <= R1) }
	F2Closure = { fd for fd in FClosure if (fd.lhs <= R2) and (fd.rhs <= R2) }

	return (R1, R2, F1Closure, F2Closure)

out = []
# Do a recursive BCNF Decomposition, and print out the results
def bcnf(R, FClosure):
	global out
	keys = findKeys(R, FClosure)
	if not isInBCNF(R, FClosure, keys): 
		print "".join(R) + " is not in BCNF"
		fd = findSmallestViolatingFD(R, FClosure, keys)

		# Decompose using that FD
		(R1, R2, F1Closure, F2Closure) = DecomposeUsingFD(R, FClosure, fd)
		print "Decomposing " + "".join(R) + " using " + str(fd) + " into relations " + "".join(R1) + " and " + "".join(R2)

		# Recurse
		bcnf(R1, F1Closure)
		bcnf(R2, F2Closure)
	else:
		print "".join(R) + " is in BCNF"
		print list(R)
		out.append(list(R))
	return "The final list of BCNF Relations are: {}".format(out)
		

# test case
R = ['A','B','C','D']
F = {FD('B', 'C'), FD('D', 'A')}
fd1 = (['B'],['C'])
fd2 = (['D'],['A'])
allfds = [fd1, fd2]

# for output
print "-------------- Find Closure of F ---------------------"
print closure(R, allfds)
print "------------------------------------------------------"
# real closure
Fclosure = Rclosure(R, allfds)

# keys = findKeys(R, Fclosure)
# print "Keys are:"
# for i in keys:
# 	print "".join(i)

# candidatekeys = findCandidateKeys(R, Fclosure)
# print "Candidate Keys are:"
# for i in candidatekeys:
# 	print "".join(i)


# print "Checking if the schema is in BCNF"
# if isInBCNF(R, Fclosure, keys):
# 	print "The schema is in BCNF"

# (R1, R2, F1Closure, F2Closure) = DecomposeUsingFD(R, Fclosure, FD('D','A'))
# print "Decomposing using " + str(FD('D','A')) + " into relations " + "".join(R1) + " and " + "".join(R2)

print "-------------- Doing a full BCNF Decompisition -------"
print bcnf(R, Fclosure)
print "------------------------------------------------------"
