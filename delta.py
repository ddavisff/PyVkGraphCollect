import math
import base36
import zlib
import gzip


class __normalization__(object):
	
	def __init__(self, array, frame_amount=10, data_input=[], data_output=[]):
		
		self.array = array.reverse()

		self.frame_amount = frame_amount
		
		frame_length = math.ceil(len(array) / frame_amount)

		self.data_input = data_input
		self.data_output = data_output

		for frame in range(frame_amount):
			self.data_input.append(array[int(frame*frame_length):int((frame+1)*frame_length)])

	def encode_int(self):
		for l in self.data_input:
			data_processed = []
			for value in range(len(l)):
				if value < len(l)-1:
					data_processed.append(base36.dumps(l[value]-l[value+1]))
				else:
					data_processed.insert(len(l), base36.dumps(l[-1]))
			self.data_output.append(data_processed)

		return self.data_output

	def decode_int(self):
		for l in self.data_input:
			data_processed = []
			for value in range(len(l)):
				if value < len(l)-1:
					data_processed.append(base36.loads(l[value]+l[value+1]))
			
			self.data_output.append(data_processed)

		return self.data_output


