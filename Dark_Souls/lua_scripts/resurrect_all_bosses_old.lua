{$lua}
if syntaxcheck then return end

[ENABLE]
local flagsBase = {
14000800, -- Iudex Gundyr - Defeated
14000801, -- Iudex Gundyr - Encountered
14000802, -- Iudex Gundyr - Pulled Sword Out
13000800, -- Vordt of the Boreal Valley - Defeated
13000801, -- Vordt of the Boreal Valley - Encountered
13100800, -- Curse-Rotted Greatwood - Defeated
13100801, -- Curse-Rotted Greatwood - Encountered
13300850, -- Crystal Sage - Defeated
13300852, -- Crystal Sage - Encountered
13500800, -- Deacons of the Deep - Defeated
13500801, -- Deacons of the Deep - Encountered
13300800, -- Abyss Watchers - Defeated
13300801, -- Abyss Watchers - Encountered
13800800, -- High Lord Wolnir - Defeated
13800801, -- High Lord Wolnir - Encountered
13800830, -- Old Demon King - Defeated
13900800, -- Yhorm the Giant - Defeated
13900801, -- Yhorm the Giant - Encountered
13700850, -- Pontiff Sulyvahn - Defeated
13700800, -- Aldrich, Devourer of Gods - Defeated
13000890, -- Dancer of the Boreal Valley - Defeated
13000830, -- Oceiros, the Consumed King - Defeated
13000838, -- Oceiros, the Consumed King - Encountered
14000830, -- Champion Gundyr - Defeated
14000831, -- Champion Gundyr - Encountered
13200800, -- Ancient Wyvern - Defeated
13200850, -- Nameless King - Defeated
13010800, -- Dragonslayer Armour - Defeated
13410830, -- Twin Princes - Defeated
13410831, -- Twin Princes - Encountered
14100800, -- Soul of Cinder - Defeated
14100801, -- Soul of Cinder - Encountered
}
local flagsDLC1 = {
14500860, -- Champion's Gravetender - Defeated
14500861, -- Champion's Gravetender - Encountered
14500620, -- Father Ariandel and Sister Friede - Unlock Ariendel's Room
14500800, -- Father Ariandel and Sister Friede - Defeated
14500801, -- Father Ariandel and Sister Friede - Encountered
}
local flagsDLC2 = {
15000800, -- Demon Prince - Defeated
15100801, -- Halflight, Spear of the Church - Encountered
15100800, -- Halflight, Spear of the Church - Defeated
15100851, -- Darkeater Midir - Encountered
15100850, -- Darkeater Midir - Defeated
15110801, -- Slave Knight Gael - Encountered
15110800 -- Slave Knight Gael - Defeated
}

local flags = {flagsBase}
if readByte(readQword("CSDlc")+0x11) == 1 then table.insert(flags, flagsDLC1) end
if readByte(readQword("CSDlc")+0x12) == 1 then table.insert(flags, flagsDLC2) end

ef.runThread2 = true
local thread = createThread(function()
	local results = {}
  local total = 0
	for i,v in ipairs(flags) do
		if not ef.runThread2 then break end
  	n = #v
    table.insert(results, n)
    local p1, p2, count = 0, 0
    local t = os.clock()
    for i,v in ipairs(v) do
		  if not ef.runThread2 then break end
      ef.setFlag(v, 0)
      p1 = i*100//n
      if p1 ~= p2 then print(p1.."% "..(os.clock() - t)*100//1/100) p2 = p1 end
    end
	end
  for i,v in ipairs(results) do total = total + v end
  print(string.format("Set %s flags!", total))
	ef.runThread2 = false
end)

[DISABLE]
ef.runThread2 = false