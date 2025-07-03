[ENABLE]
{$lua}
local playerHPAddr   = getAddress("[[[[DarkSoulsIII.exe+04543F60]+28]+3A0]+70]+90")
local playerHP    = readInteger(playerHPAddr) or 0



if playerHP > 0 then
local al = getAddressList()

local rangeRec = al.getMemoryRecordByDescription("Increase LockOn Range")
local timerRec = al.getMemoryRecordByDescription("Line Of Sight LockOn Deactivate Time")

if rangeRec then
  rangeRec.Value = "100"
  rangeRec.Frozen = true
end

if timerRec then
  timerRec.Value = "200"
  timerRec.Frozen = true
end
end

{$asm}

[DISABLE]
{$lua}

  local al = getAddressList()

local rangeRec = al.getMemoryRecordByDescription("Increase LockOn Range")
local timerRec = al.getMemoryRecordByDescription("Line Of Sight LockOn Deactivate Time")

if rangeRec then
  rangeRec.Value = "0"
  rangeRec.Frozen = false
end

if timerRec then
  timerRec.Value = "0"
  timerRec.Frozen = false
end
{$asm}
