-- 
--  spriter.lua
--  sprinter-moai
--  
--  Created by Jon Baker on 2012-11-09.
--  Distributed under MPL-2.0 licence (http://opensource.org/licenses/MPL-2.0)
-- 

local texture
local curves = {}

local function insertProps ( self, layer )

	for i, v in ipairs ( self.props ) do
		layer:insertProp ( v )
	end
end

local function removeProps ( self, layer )

	for i, v in ipairs ( self.props ) do
		layer:removeProp ( v )
	end
end

local function createAnim ( self, name )

	local layerSize = 8;

	local player = MOAIAnim.new ()
	player:reserveLinks ( (#self.curves[name] * layerSize) )
	
	local root = MOAITransform.new ()
	local props = {}
	
	print("Set Animation:", name)
	
	for i, curveSet in pairs ( self.curves[name] ) do
		local prop = MOAIProp2D.new ()
		prop:setParent ( root )
		prop:setDeck ( texture )
		prop:setPriority( curveSet.priority )
		
		local c = ( i - 1 ) * layerSize
		player:setLink ( c + 1, curveSet.id, prop, MOAIProp2D.ATTR_INDEX )
		player:setLink ( c + 2, curveSet.x, prop, MOAITransform.ATTR_X_LOC )
		player:setLink ( c + 3, curveSet.y, prop, MOAITransform.ATTR_Y_LOC )
		player:setLink ( c + 4, curveSet.r, prop, MOAITransform.ATTR_Z_ROT )
		player:setLink ( c + 5, curveSet.xs, prop, MOAITransform.ATTR_X_SCL )
		player:setLink ( c + 6, curveSet.ys, prop, MOAITransform.ATTR_Y_SCL )
		player:setLink ( c + 7, curveSet.px, prop, MOAITransform.ATTR_X_PIV )
		player:setLink ( c + 8, curveSet.py, prop, MOAITransform.ATTR_Y_PIV )
		table.insert ( props, prop )
	end

	player:setMode(MOAITimer.LOOP)

	player.root = root
	player.props = props
	
	player.insertProps = insertProps
	player.removeProps = removeProps
	
	player:apply ( 0 )
	
	return player
end

function spriter(filename, deck, names)
	local anims = dofile ( filename )
	curves = {}
	texture = deck 
	for anim, objects in pairs ( anims ) do
		print(string.format("Loading %s", anim))
		
		local animCurves = {}
		
	    for i, object in pairs ( objects ) do
			local numKeys = #object

		    -- Texture ID
		    local idCurve = MOAIAnimCurve.new ()
			idCurve:reserveKeys ( numKeys )

		    -- Location
			local xCurve = MOAIAnimCurve.new ()
			xCurve:reserveKeys ( numKeys )

			local yCurve = MOAIAnimCurve.new ()
			yCurve:reserveKeys ( numKeys )

		    -- Rotation
			local rCurve = MOAIAnimCurve.new ()
			rCurve:reserveKeys ( numKeys )

		    -- Scale
			local sxCurve = MOAIAnimCurve.new ()
			sxCurve:reserveKeys ( numKeys )

			local syCurve = MOAIAnimCurve.new ()
			syCurve:reserveKeys ( numKeys )

		    -- Pivot
		    local pxCurve = MOAIAnimCurve.new ()
			pxCurve:reserveKeys ( numKeys )

			local pyCurve = MOAIAnimCurve.new ()
			pyCurve:reserveKeys ( numKeys )
		
		
	        for ii, frame in pairs ( object ) do
				if frame.texture then
					time = frame.time / 1000
					--printf("Frame %d,  time: %s, texture: %s, x: %d, y: %d, r: %4f, sx: %4f, sy: %4f, px: \n", ii, time, frame.texture, frame.x, frame.y, frame.angle, frame.scale_x, frame.scale_y)
					idCurve:setKey ( ii, time, names[frame.texture], MOAIEaseType.FLAT)
					xCurve:setKey  ( ii, time, frame.x, MOAIEaseType.FLAT)
					yCurve:setKey  ( ii, time, frame.y, MOAIEaseType.FLAT)
					rCurve:setKey  ( ii, time, frame.angle, MOAIEaseType.FLAT)
					sxCurve:setKey ( ii, time, frame.scale_x, MOAIEaseType.FLAT)
					syCurve:setKey ( ii, time, frame.scale_y, MOAIEaseType.FLAT)
					pxCurve:setKey ( ii, time, frame.pivot_x, MOAIEaseType.FLAT )
					pyCurve:setKey ( ii, time, frame.pivot_y, MOAIEaseType.FLAT )
				end
	        end
	
			local curveSet = {}

			curveSet.id = idCurve
			curveSet.x = xCurve
			curveSet.y = yCurve
			curveSet.r = rCurve
			curveSet.xs = sxCurve
			curveSet.ys = syCurve
			curveSet.px = pxCurve
			curveSet.py = pyCurve
			curveSet.priority = object[1].zindex
			table.insert ( animCurves, curveSet )			
			
	    end
		curves[anim] = animCurves
		
	end
	
	local sprite = {}
	sprite.curves = curves
	sprite.createAnim = createAnim

	return sprite
	
end