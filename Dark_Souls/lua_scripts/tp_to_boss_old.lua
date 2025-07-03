[ENABLE]
{$lua}
-- Define pointer strings
local PLAYER_HEALTH_PTR_STR = "[[[[WorldChrMan]+80]+1F90]+18]+D8"
local LUDEX_TARGET_STR       = "[[[WorldChrMan]+40]+28]+80"
local CURRENT_ANGLE_PTR      = "[[[WorldChrMan]+40]+28]+74"

writeBytes(LUDEX_TARGET_STR,
  0x93, 0xE6, 0xF8, 0x42,
  0x6D, 0xD0, 0x7F, 0xC2,
  0xC7, 0xF3, 0x0A, 0x44
)
print("[TP] Teleported Successfully!")


-- Set desired angle
local targetAngle = -2.778103352
local angleAddr = getAddressSafe(CURRENT_ANGLE_PTR)
if angleAddr then
  writeFloat(angleAddr, targetAngle)
  print("Player angle set to:", targetAngle)
else
  print("ERROR: Could not resolve angle pointer!")
  getScript().Active = false
  return
end


-- Automatically disable this script so it runs only once
getScript().Active = false
{$asm}

[DISABLE]
{$lua}

{$asm}
