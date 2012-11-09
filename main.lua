require 'lib/tpsloader'
require 'lib/spriter'
require 'lib/utils'

MOAISim.openWindow ( "test", 960, 960 )

viewport = MOAIViewport.new ()
viewport:setSize ( 960, 960 )
viewport:setScale ( 960, 960 )

layer = MOAILayer2D.new ()
layer:setViewport ( viewport )
MOAISim.pushRenderPass ( layer )

gfxQuads, names = tpsloader ( 'monster.lua', 'monster.png' )
sprite = spriter("example.lua", gfxQuads, names)

anim = sprite:createAnim ( "Posture" )
--anim = sprite:createAnim ( "Idle" )
anim:insertProps ( layer )
anim:start ()
