# rvect.py
#
# Purpose:
#	Manipulate lists in a manner similar to the way in which
#	lists ('vectors') are handled in R.
#
# Author:
#	Dreas Nielsen (RDN)
#
# Copyright and license:
#	Copyright (c) 2007, 2009, R.Dreas Nielsen
#	This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#   The GNU General Public License is available at <http://www.gnu.org/licenses/>
#
# Notes:
#   1. This module contains several functions that implement basic
#		listwise operations (e.g., and, or, sum, product) on lists or
#		tuples, plus a class ('Rvect') that defines overloaded operators
#		for these and other functions.
#	2. The functionality of the 'Rvect' class is intended to mimic the
#		operation of "vectors" in R (http://www.r-project.org/).
#		The class does not, however, provide any kind of interface to R,
#		nor does the class entirely mimic R vectors.
#		(RPy [http://rpy.sourceforge.net/] provides an interface to R.)
#		For example, whereas elements of an R vector must all
#		be of the same type, the Rvect class has no such constraint--
#		Rvect elements may be of any type, as with a Python list.  
#		The class does contain methods to coerce all elements to several
#		specific types, however.
#	3. Because Python does not allow a class to define its own __not__ method,
#		the command
#			not Rvect()
#		does not work as might be expected.  Instead, there is a method named
#			.logical_not()
#		of an Rvect object that must be called instead.
#	4. Because Python implements the logical binary infix operations 'and',
#		'or', and 'xor' by calling __nonzero__ or __len__ on each object and then
#		executing the Boolean logic itself, logical binary combination
#		of Rvect objects cannot be done using the 'and' infix operator.
#		Instead, the following functions are defined:
#			.logical_and(Rvect1, Rvect2, ...)
#			.logical_or(Rvect1, Rvect2, ...)
#			.logical_xor(...)
#	5. The special methods __and__, __or__, and __xor__, which correspond to the
#		binary infix operators '&', '|', and '^',are for binary, not logical,
#		comparisons.  In R, however, these infix operators peform logical
#		comparisons.  Therefore, the special methods have been implemented
#		so that they convert their arguments to booleans, and therefore correspond
#		to logical operators, and so operate similarly to the equivalent
#		R operators.  Thus, for Rvects a and b, the following two expressions
#		are equivalent:
#				a.logical_and(b)
#				a & b
#		Both return a vector of booleans.  As per note 5, these are *not*
#		equivalent to
#				a and b
#		which returns a single boolean value.
#	6. The 'list_...()' functions in this module allow operation on multiple
#		lists, whereas the binary infix mathematical operators implemented
#		for Rvect instances only allow operation on two objects.  For example,
#		multiple lists can 	be summed in parallel with
#			list_sum(list1, list2, list3,...)
#		However, the arguments to the 'list_...()' functions must all be lists
#		of the same length, whereas the arguments to the Rvect methods may
#		be other Rvect objects, lists, or scalars.
#
# Examples:
#	1. Multiplying by a scalar
#		>>> [1, 2, 3] * 2
#		[1, 2, 3, 1, 2, 3]
#		>>> Rvect([1, 2, 3]) * 2
#		[2, 4, 6]
#	2. Adding a scalar
#		>>> [1, 2, 3] + 2
#		TypeError
#		>>> Rvect([1, 2, 3]) + 2
#		[3, 4, 5]
#	3. Multiplying two lists or vectors
#		>>> [1, 2, 3] * [4, 5, 6]
#		TypeError
#		>>> Rvect([1, 2, 3]) * Rvect([4, 5, 6])
#		[4, 10, 18]
#	4. Adding two lists or vectors
#		>>> [1, 2, 3] + [4, 5, 6]
#		[1, 2, 3, 4, 5, 6]
#		>>> Rvect([1, 2, 3]) + Rvect([4, 5, 6])
#		[5, 7, 9]
#	5. Binary logical operations on two lists or vectors
#		>>> [True, True, False, False] and [True, False, True, False]
#		[True, False, True, False]
#		>>> list_and( [True, True, False, False], [True, False, True, False] )
#		[True, False, False, False]
#		>>> Rvect([True, True, False, False]).logical_and( Rvect([True, False, True, False]) )
#		[True, False, False, False]
#
# History:
#	 Date		 Comments
#	----------	----------------------------------
#	12/22/2007	Created.  RDN.
#	12/23/2007	Added more type conversion and the regex matching functions.  RDN.
#	12/24/2007	Added 'all_list_len()' to factor out common code from most of the 'list_...()'
#				routines.  Added some documentation in the file header.  RDN.
#	12/29/2007	Implemented __and__, __or__, and __xor__.  RDN.
#	1/10/2009	Corrected typo in examples.  RDN.
#=================================================================================

import types

__version = "0.1.0.0"

class RvectorError(Exception):
	pass

__BAD_NARGS_MSG = "Incorrect number of arguments"
__BAD_LEN_MSG = "Arguments have different lengths"

def rep(item, ntimes):
	"""Return a list with 'item' repeated 'ntimes' times."""
	return [ item for n in range(ntimes) ]

def all_equal(list1):
	"""Return True if all elements of the list are equal, False otherwise."""
	if list1:
		for i in range(1, len(list1)):
			if list1[i] != list1[0]:
				return False
	return True

def as_boolean(list1):
	return [ bool(v) for v in list1 ]

def check_minargs(min, *args):
	if len(args) < min:
		raise RvectorError, __BAD_NARGS_MSG

def check_lengths(*lists):
	if lists:
		if not all_equal([len(a) for a in lists]):
			raise RvectorError, __BAD_LEN_MSG

def __apply(func, index, *lists):
	d = [ l[index] for l in lists ]
	return reduce(func, d)

def list_not(list1):
	return [ not bool(v) for v in list1 ]

def all_list_len(mincount, *lists):
	"""Return the length of the lists, after a check to ensure that there are at least 'mincount'
	lists provided, and that they are all of the same length."""
	check_minargs(mincount, *lists)
	check_lengths(*lists)
	return len(lists[0])

def list_and(*lists):
	return [ __apply(lambda a, b: bool(a) and bool(b), i, *lists) for i in range(all_list_len(2, *lists)) ]

def list_or(*lists):
	return [ __apply(lambda a, b: bool(a) or bool(b), i, *lists) for i in range(all_list_len(2, *lists)) ]

def list_xor(*lists):
	return [ __apply(lambda a, b: bool(a) ^ bool(b), i, *lists) for i in range(all_list_len(2, *lists)) ]

def list_sum(*lists):
	return [ __apply(lambda a, b: a + b, i, *lists) for i in range(all_list_len(2, *lists)) ]

def list_prod(*lists):
	return [ __apply(lambda a, b: a * b, i, *lists) for i in range(all_list_len(2, *lists)) ]

def list_diff(*lists):
	return [ __apply(lambda a, b: a - b, i, *lists) for i in range(all_list_len(2, *lists)) ]

def list_div(*lists):
	return [ __apply(lambda a, b: a / b, i, *lists) for i in range(all_list_len(2, *lists)) ]

def list_floatdiv(*lists):
	return [ __apply(lambda a, b: float(a) / float(b), i, *lists) for i in range(all_list_len(2, *lists)) ]

def list_floordiv(*lists):
	return [ __apply(lambda a, b: a // b, i, *lists) for i in range(all_list_len(2, *lists)) ]

def list_mod(*lists):
	return [ __apply(lambda a, b: a % b, i, *lists) for i in range(all_list_len(2, *lists)) ]

def list_eq(*lists):
	return [ __apply(lambda a, b: a == b, i, *lists) for i in range(all_list_len(2, *lists)) ]

def list_ne(*lists):
	return [ __apply(lambda a, b: a != b, i, *lists) for i in range(all_list_len(2, *lists)) ]

def list_lt(*lists):
	return [ __apply(lambda a, b: a < b, i, *lists) for i in range(all_list_len(2, *lists)) ]

def list_le(*lists):
	return [ __apply(lambda a, b: a <= b, i, *lists) for i in range(all_list_len(2, *lists)) ]

def list_gt(*lists):
	return [ __apply(lambda a, b: a > b, i, *lists) for i in range(all_list_len(2, *lists)) ]

def list_ge(*lists):
	return [ __apply(lambda a, b: a >= b, i, *lists) for i in range(all_list_len(2, *lists)) ]

def list_matches(regex, list1):
	"""Return a list of booleans indicating whether the regex matches each element of the list.

	Note that this uses re.search() rather than re.match(), so the regular expression
	need not match at the beginning of the list elements"""
	return [ regex.search(elem) != None for elem in list1 ]

def is_rvect(object):
	if type(object) == types.InstanceType and isinstance(object, Rvect):
		return True
	return False

def as_lists(fixed_length, *args):
	"""Convert the arguments into a tuple of lists.  All must have a length
	of fixed_length.  Atomic arguments are converted to a list of booleans
	having the specified length."""
	listargs = []
	for v in args:
		tpv = type(v)
		if is_rvect(v):
			if len(v.seq) != fixed_length:
				raise RvectorError, __BAD_LEN_MSG
			listargs.append(v.seq)
		elif tpv == types.ListType or tpv == types.TupleType:
			if len(v) != fixed_length:
				raise RvectorError, __BAD_LEN_MSG
			listargs.append(list(v))
		else:
			listargs.append( rep(bool(v), fixed_length ) )
	return listargs

class Rvect():
	def __init__(self, sequence):
		st = type(sequence)
		if st == types.ListType:
			self.seq = sequence
		elif  st == types.TupleType:
			self.seq = list(sequence)
		else:
			self.seq = [ sequence ]
		self.__index = 0
	def next(self):
		if self.__index >= len(self.seq):
			self.__index = 0
			raise StopIteration
		else:
			self.__index += 1
			return self.seq[self.__index - 1]
	def __repr__(self):
		return self.seq.__repr__()
	def __str__(self):
		return self.seq.__str__()
	def __len__(self):
		return len(self.seq)
	def __nonzero__(self):
		return len(self.seq) > 0
	def __getitem__(self, key):
		return self.seq[key]
	def __setitem__(self, key, value):
		self.seq[key] = value
	def __delitem__(self, key):
		del self.seq[key]
	def __iter__(self):
		return self
	def __contains__(self, key):
		return key in self.seq
	def __lt__(self, other):
		tpo = type(other)
		if is_rvect(other):
			return Rvect(list_lt(self.seq, other.seq))
		elif tpo == types.ListType or tpo == types.TupleType:
			return Rvect(list_lt(self.seq, other))
		else:
			return Rvect(list_lt(self.seq, [ other ] ))
	def __le__(self, other):
		tpo = type(other)
		if is_rvect(other):
			return Rvect(list_le(self.seq, other.seq))
		elif tpo == types.ListType or tpo == types.TupleType:
			return Rvect(list_le(self.seq, other))
		else:
			return Rvect(list_le(self.seq, [ other ] ))
	def __eq__(self, other):
		tpo = type(other)
		if is_rvect(other):
			return Rvect(list_eq(self.seq, other.seq))
		elif tpo == types.ListType or tpo == types.TupleType:
			return Rvect(list_eq(self.seq, other))
		else:
			return Rvect(list_eq(self.seq, [ other ] ))
	def __ne__(self, other):
		tpo = type(other)
		if is_rvect(other):
			return Rvect(list_ne(self.seq, other.seq))
		elif tpo == types.ListType or tpo == types.TupleType:
			return Rvect(list_ne(self.seq, other))
		else:
			return Rvect(list_ne(self.seq, [ other ] ))
	def __gt__(self, other):
		tpo = type(other)
		if is_rvect(other):
			return Rvect(list_gt(self.seq, other.seq))
		elif tpo == types.ListType or tpo == types.TupleType:
			return Rvect(list_gt(self.seq, other))
		else:
			return Rvect(list_gt(self.seq, [ other ] ))
	def __ge__(self, other):
		tpo = type(other)
		if is_rvect(other):
			return Rvect(list_ge(self.seq, other.seq))
		elif tpo == types.ListType or tpo == types.TupleType:
			return Rvect(list_ge(self.seq, other))
		else:
			return Rvect(list_ge(self.seq, [ other ] ))
	def __add__(self, other):
		tpo = type(other)
		if is_rvect(other):
			return Rvect(list_sum(self.seq, other.seq))
		elif tpo == types.ListType or tpo == types.TupleType:
			return Rvect(list_sum(self.seq, other))
		elif tpo == types.IntType or tpo == types.FloatType:
			return Rvect( [ other + self.seq[i] for i in range(len(self.seq)) ] )
		else:
			try:
				onum = float(other)
			except:
				raise ValueError
			return Rvect( [ onum + self.seq[i] for i in range(len(self.seq)) ] )
	def __sub__(self, other):
		tpo = type(other)
		if is_rvect(other):
			return Rvect(list_diff(self.seq, other.seq))
		elif tpo == types.ListType or tpo == types.TupleType:
			return Rvect(list_diff(self.seq, other))
		elif tpo == types.IntType or tpo == types.FloatType:
			return Rvect( [ self.seq[i] - other for i in range(len(self.seq)) ] )
		else:
			try:
				onum = float(other)
			except:
				raise ValueError
			return Rvect( [ self.seq[i] - onum for i in range(len(self.seq)) ] )
	def __mul__(self, other):
		tpo = type(other)
		if is_rvect(other):
			return Rvect(list_prod(self.seq, other.seq))
		elif tpo == types.ListType or tpo == types.TupleType:
			return Rvect(list_prod(self.seq, other))
		elif tpo == types.IntType or tpo == types.FloatType:
			return Rvect( [ other * self.seq[i] for i in range(len(self.seq)) ] )
		else:
			try:
				onum = float(other)
			except:
				raise ValueError
			return Rvect( [ onum * self.seq[i] for i in range(len(self.seq)) ] )
	def __div__(self, other):
		tpo = type(other)
		if is_rvect(other):
			return Rvect(list_div(self.seq, other.seq))
		elif tpo == types.ListType or tpo == types.TupleType:
			return Rvect(list_div(self.seq, other))
		elif tpo == types.IntType or tpo == types.FloatType:
			return Rvect( [ self.seq[i] / other for i in range(len(self.seq)) ] )
		else:
			try:
				onum = float(other)
			except:
				raise ValueError
			return Rvect( [ self.seq[i] / onum for i in range(len(self.seq)) ] )
	def __truediv__(self, other):
		tpo = type(other)
		if is_rvect(other):
			return Rvect(list_floatdiv(self.seq, other.seq))
		elif tpo == types.ListType or tpo == types.TupleType:
			return Rvect(list_floatdiv(self.seq, other))
		else:
			try:
				onum = float(other)
			except:
				raise ValueError
			return Rvect( [ self.seq[i] / onum for i in range(len(self.seq)) ] )
	def __floordiv__(self, other):
		tpo = type(other)
		if is_rvect(other):
			return Rvect(list_floordiv(self.seq, other.seq))
		elif tpo == types.ListType or tpo == types.TupleType:
			return Rvect(list_floordiv(self.seq, other))
		elif tpo == types.IntType or tpo == types.FloatType:
			return Rvect( [ self.seq[i] // other for i in range(len(self.seq)) ] )
		else:
			try:
				onum = float(other)
			except:
				raise ValueError
			return Rvect( [ self.seq[i] // onum for i in range(len(self.seq)) ] )
	def __mod__(self, other):
		tpo = type(other)
		if is_rvect(other):
			return Rvect(list_mod(self.seq, other.seq))
		elif tpo == types.ListType or tpo == types.TupleType:
			return Rvect(list_mod(self.seq, other))
		elif tpo == types.IntType or tpo == types.FloatType:
			return Rvect( [ self.seq[i] % other for i in range(len(self.seq)) ] )
		else:
			try:
				onum = float(other)
			except:
				raise ValueError
			return Rvect( [ self.seq[i] % onum for i in range(len(self.seq)) ] )
	def __divmod__(self, other):
		return NotImplemented
	def __pow__(self, other):
		return NotImplemented
	def __lshift__(self, other):
		return NotImplemented
	def __rshift__(self, other):
		return NotImplemented
	def logical_not(self):
		return Rvect( list_not(self.seq) )
	def logical_and(self, *vectors):
		return Rvect( list_and(self.seq, *tuple(as_lists(len(self.seq), *vectors)) ) )
	def logical_or(self, *vectors):
		return Rvect( list_or(self.seq, *tuple(as_lists(len(self.seq), *vectors)) ) )
	def logical_xor(self, *vectors):
		return Rvect( list_xor(self.seq, *tuple(as_lists(len(self.seq), *vectors)) ) )
	def __and__(self, other):
		return Rvect( list_and( *tuple(as_lists(len(self.seq), as_boolean(self.seq), as_boolean(other))) ) )
	def __or__(self, other):
		return Rvect( list_or( *tuple(as_lists(len(self.seq), as_boolean(self.seq), as_boolean(other))) ) )
	def __xor__(self, other):
		return Rvect( list_xor( *tuple(as_lists(len(self.seq), self.seq, other)) ) )
	def __radd__(self, other):
		return self.__add__(other)
	def __rsub__(self, other):
		tpo = type(other)
		if is_rvect(other):
			return Rvect(list_diff(other.seq, self.seq))
		elif tpo == types.ListType or tpo == types.TupleType:
			return Rvect(list_diff(other, self.seq))
		elif tpo == types.IntType or tpo == types.FloatType:
			return Rvect( [ other - self.seq[i] for i in range(len(self.seq)) ] )
		else:
			try:
				onum = float(other)
			except:
				raise ValueError
			return Rvect( [ onum - self.seq[i] for i in range(len(self.seq)) ] )
	def __rmul__(self, other):
		return self.__mul__(other)
	def __rdiv__(self, other):
		tpo = type(other)
		if is_rvect(other):
			return Rvect(list_div(other.seq, self.seq))
		elif tpo == types.ListType or tpo == types.TupleType:
			return Rvect(list_div(other, self.seq))
		elif tpo == types.IntType or tpo == types.FloatType:
			return Rvect( [ other / self.seq[i] for i in range(len(self.seq)) ] )
		else:
			try:
				onum = float(other)
			except:
				raise ValueError
			return Rvect( [ onum / self.seq[i] for i in range(len(self.seq)) ] )
	def __rtruediv__(self, other):
		return self.__rdiv__(other)
	def __rfloordiv__(self, other):
		tpo = type(other)
		if is_rvect(other):
			return Rvect(list_floordiv(other.seq, self.seq))
		elif tpo == types.ListType or tpo == types.TupleType:
			return Rvect(list_floordiv(other, self.seq))
		elif tpo == types.IntType or tpo == types.FloatType:
			return Rvect( [ other // self.seq[i] for i in range(len(self.seq)) ] )
		else:
			try:
				onum = float(other)
			except:
				raise ValueError
			return Rvect( [ onum // self.seq[i] for i in range(len(self.seq)) ] )
	def __rmod__(self, other):
		tpo = type(other)
		if is_rvect(other):
			return Rvect(list_mod(other.seq, self.seq))
		elif tpo == types.ListType or tpo == types.TupleType:
			return Rvect(list_mod(other, self.seq))
		elif tpo == types.IntType or tpo == types.FloatType:
			return Rvect( [ other % self.seq[i] for i in range(len(self.seq)) ] )
		else:
			try:
				onum = float(other)
			except:
				raise ValueError
			return Rvect( [ onum %self.seq[i] for i in range(len(self.seq)) ] )
	def __rdivmod__(self, other):
		return NotImplemented
	def __rpow__(self, other):
		return NotImplemented
	def __rlshift__(self, other):
		return NotImplemented
	def __rrshift__(self, other):
		return NotImplemented
	def __neg__(self):
		self.seq = [ -1 * x for x in self.seq ]
		return self
	def __abs__(self):
		self.seq = [ abs(x) for x in self.seq ]
		return self
	def as_intvect(self):
		return Rvect([ int(x) for x in self.seq ])
	def as_floatvect(self):
		return Rvect([ float(x) for x in self.seq ])
	def as_strvect(self):
		return Rvect([ str(x) for x in self.seq ])
	def as_boolvect(self):
		return Rvect( as_boolean(self.seq) )
	def as_list(self):
		return self.seq
	def as_tuple(self):
		return tuple(self.seq)
	def matches( self, regex ):
		"""Return an Rvect of booleans indicating whether the regular expression matches each element."""
		return Rvect( list_matches( regex, self.seq ) )
