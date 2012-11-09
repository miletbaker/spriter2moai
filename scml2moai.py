#!/usr/bin/env python

# 
#  scml2moai.py
#  sprinter-moai
#  
#  Created by Jon Baker on 2012-11-09.
#  Distributed under MPL-2.0 licence (http://opensource.org/licenses/MPL-2.0)
# 

# TODO: fix rotations use spin when collecting data
# TODO: Work out bone multipliers

import xml.sax
import sys
import re
from collections import OrderedDict
from optparse import OptionParser

class SaxHandler (xml.sax.handler.ContentHandler):
	def __init__ (self):
		self.tags = []
		self.folders = {}
		self.folder = 0
		self.files = {}
		self.animations = {}
		self.animation_name = None
		self.timelines = OrderedDict()
		self.timeline = 0
		self.key = 0

	def startElement (self, name, attrs):
		# Track current tag
		self.tags.append(name)
		
		# Parse SCML Information
		if name == 'folder':
			self.folder = attrs.getValue('id')
			
		elif name == 'file':
			self.files[attrs.getValue('id')] = { 'file': re.sub(r'.*/', '', attrs.getValue('name')), 'width': attrs.getValue('width'), 'height': attrs.getValue('height') }
			
		elif name == 'animation':
			# Store each animation
			loop = False if attrs.getValue('looping') == 'false' else True
			self.animation_name = attrs.getValue('name')
			self.animations[self.animation_name] = { 'loop' : loop , 'length' : attrs.getValue('length') }
			
		elif name == 'object_ref' and self.tags[-3] == "mainline":
			# Get zindexes from mainline and store by [timesline][key]
			timeline = attrs.getValue('timeline')
			keys = self.timelines[timeline] if self.timelines.has_key(timeline) else OrderedDict()
			keys[attrs.getValue('key')] = { 'zindex': attrs.getValue('z_index') }
			self.timelines[timeline] = keys
			
		elif name == "timeline":
		 	self.timeline = attrs.getValue('id')
		
		elif name == "key" and self.tags[-2] == "timeline":
			# Collect useful information from key tag and stash keyframe
			self.key = attrs.getValue('id')
			if self.timelines.has_key(self.timeline) and self.timelines[self.timeline].has_key(self.key):
				keyframe = self.timelines[self.timeline][self.key]
				keyframe['spin'] = attrs.getValue('spin') if attrs.has_key('spin') else 0
				keyframe['time'] = attrs.getValue('time') if attrs.has_key('time') else 0
				self.timelines[self.timeline][self.key] = keyframe
				
		elif name == "object" and self.tags[-3] == "timeline":
			# retrieve keyframe and populate with data from object tag
			if self.timelines.has_key(self.timeline) and self.timelines[self.timeline].has_key(self.key):
				keyframe = self.timelines[self.timeline][self.key]
				file_details = self.folders[attrs.getValue('folder')][attrs.getValue('file')]
				keyframe['texture'] = file_details['file']
				keyframe['x'] = attrs.getValue('x') if attrs.has_key('x') else 0
				keyframe['y'] = attrs.getValue('y') if attrs.has_key('y') else 0
				
				keyframe['angle'] = attrs.getValue('angle') if attrs.has_key('angle') else 0
				keyframe['scale_x'] = attrs.getValue('scale_x') if attrs.has_key('scale_x') else 1
				keyframe['scale_y'] = attrs.getValue('scale_y') if attrs.has_key('scale_y') else 1
				keyframe['pivot_x'] = (float(file_details['width']) * float(attrs.getValue('pivot_x'))) if attrs.has_key('pivot_x') else 0
				keyframe['pivot_y'] = (float(file_details['height']) * float(attrs.getValue('pivot_y'))) if attrs.has_key('pivot_y') else float(file_details['height'])
				self.timelines[self.timeline][self.key] = keyframe


	def endElement (self, name):
		self.tags.pop()
		if name == 'folder':
			# store all files for ending folder
			self.folders[self.folder] = self.files
			self.files = {}
			
		elif name == "animation":
			# store mainline for ending animation
			self.animations[self.animation_name] = self.timelines #OrderedDict(sorted(self.timelines.items(), key=lambda t: t[0]))
			self.timelines = {}		

#---

def output_lua(anim_data, outpath, scale):
	# Open file for writing
	f = open(outpath, 'w')
	print "Writing animation to %s" % outpath

	f.write('local anim = {\n')

	for i, animation in enumerate(anim_data.keys()):
		# Generate each animation
		timelines = anim_data[animation]
		f.write('\t[\'%s\'] = {\n' % animation )
		
		for ii, timeline in enumerate(timelines.values()):	
			# Generate Each object layer
			f.write('\t\t[%d] = {\n' % (ii + 1))
			
			for iii, keyframe in enumerate(timeline.values()):
				# Generate each keyframe
				f.write('\t\t\t[%d] = {\n' % (iii + 1))
				iv = 0
				
				for anim_property, value in keyframe.items():
					# Generate each property
					iv += 1
					if anim_property in ["x", "y", "pivot_x", "pivot_y"]:
						# Adjust values for scaled textures
						adjusted_val = int(round(float(value) * scale))
						f.write('\t\t\t\t[\'%s\'] = %s' % (anim_property, adjusted_val))
						
					elif anim_property == "texture":
						f.write('\t\t\t\t[\'%s\'] = \'%s\'' % (anim_property, value))
						
					elif anim_property == "angle":
						# Calculate angle delta
						new_angle = float(value)
						if iii > 0:
							prev_angle = float(timeline.values()[iii-1]['angle'])
							prev_spin = int(timeline.values()[iii-1]['spin'])
						else:
							prev_angle = 0
							prev_spin = 0
						spin = prev_spin #int(keyframe['spin'])
						if spin >= 0 and iii > 0 and new_angle != prev_angle:
							angle = new_angle - prev_angle if new_angle > prev_angle else (360 - prev_angle) + new_angle
						elif spin < 0 and iii > 0  and new_angle != prev_angle:
							angle = new_angle - prev_angle if new_angle < prev_angle else (-360 - prev_angle) + new_angle
						else:
							angle = new_angle
						#print "texture: %s, angle: %6.2f, spin: %6.2f, new_angle: %6.2f, prev_angle: %6.2f" % (keyframe['texture'], angle, spin, new_angle, prev_angle)
						f.write('\t\t\t\t[\'%s\'] = %s' % (anim_property, angle))
						prev_angle = angle
						
					else:
						f.write('\t\t\t\t[\'%s\'] = %s' % (anim_property, value))
					
					# write our closing brackets
					f.write(',\n' if iv < len(keyframe.keys()) else '\n')
				f.write('\t\t\t},\n' if iii+1 < len(timeline) else '\t\t\t}\n')
			f.write('\t\t},\n' if ii+1 < len(timelines) else '\t\t}\n')
		f.write('\t},\n' if i+1 < len(anim_data.keys()) else '\t}\n')
	f.write('}\n\nreturn anim')
	# Close file
	f.close

def main ():
	try:
		# Parser setup for command line options
		parser = OptionParser(usage = "usage: %prog file.scml [options]", version = "SCML2Moai v0.1")
		parser.add_option("-f", "--file", dest="filename",
		                  help="specify output FILE (default outputs to same name as scml file)", metavar="FILE")
		parser.add_option("-4", "--x4",
		                  action="store_true", dest="x4", default=False,
		                  help="Dimensions are based on @4x size also output @2x.lua and standard .lua files")
		parser.add_option("-2", "--x2",
		                  action="store_true", dest="x2", default=False,
		                  help="Dimensions are based on @2x size also output standard .lua files")				
		(options, args) = parser.parse_args()
		
		# Check an input file has been provided
		if len(args) >= 1:
			inpath= args[0]
		else:
			 parser.error("You must specify an SCML file to convert")
			
		# Identify filenames for lua files
		outpath = ""
		outpathx2 = None
		outpathx4 = None
		if options.filename:
			outpath = options.filename
		elif re.search(r"\.scml\Z", inpath.lower()):
			outpath = re.sub(r"\.scml\Z", ".lua", inpath.lower()) 
		else:
			outpath = inpath + ".lua"
		
		if options.x2 or options.x4:
			outpathx2 = re.sub(r"\.lua\Z", "@2x.lua", outpath) 
		if options.x4:
			outpathx4 = re.sub(r"\.lua\Z", "@4x.lua", outpath)
		
		# Parse input scml file
		handler= SaxHandler()
		xml.sax.parse (inpath, handler)
		anim_data = handler.animations
		
		# Write data to lua files
		if options.x4:
			output_lua(anim_data, outpathx4, 1)
			output_lua(anim_data, outpathx2, 0.5)
			output_lua(anim_data, outpath, 0.25)
		elif options.x2:
			output_lua(anim_data, outpathx2, 1)
			output_lua(anim_data, outpath, 0.5)
		else:
			output_lua(anim_data, outpath, 1)
		
	except IOError as e:
	    print "Error: {0}".format(e.strerror)

if __name__ == '__main__':
	main()
