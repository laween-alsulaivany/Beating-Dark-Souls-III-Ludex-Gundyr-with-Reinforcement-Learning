[ENABLE]
{$lua}

-- Resolve pointers:
local playerHPAddr   = getAddress("[[[[DarkSoulsIII.exe+04543F60]+28]+3A0]+70]+90")



if not playerHPAddr then
  print("ERROR: Could not resolve player HP pointer.")
  return
end


-- Read values:
local playerHP    = readInteger(playerHPAddr) or 0
print(playerHP)



-- If conditions are good, enable other scripts
if playerHP > 0 then
  print("Conditions met: Not in boss fight, health > 0.")
  local al = getAddressList()
  local kill = al.getMemoryRecordByDescription("Kill All Mobs")

  local estus_alloc = al.getMemoryRecordByDescription("EstusFlaskAllocateNum_byHp")
  local lockonincrease = al.getMemoryRecordByDescription("LockOnIncrease")


  if kill then kill.Active = true end
  if estus_alloc then estus_alloc.Active = true estus_alloc.Value = "4" estus_alloc.Frozen = true end
if lockonincrease then lockonincrease.Active = false lockonincrease.Active = true end

end

getScript().Active = false
{$asm}

[DISABLE]
{$lua}
{$asm}
