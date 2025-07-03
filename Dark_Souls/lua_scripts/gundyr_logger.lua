[ENABLE]
{$lua}
if myTimer then
    myTimer.destroy()
end

local file_path = "C:\\Users\\Laween\\OneDrive\\Desktop\\MSUM\\Spring_2025\\490\\Final_Project\\Dark_Souls\\FP-Machine-Learning\\Code\\data\\gundyr_info.txt"

function updateGundyrValues()
    -- Check if target_ptr exists and is valid
local target_ptr = getAddressSafe("target_ptr")
if not target_ptr then return end

local target = readPointer(target_ptr)
if not target or target == 0 then return end


    local base = readPointer(target + 0x1F90)
    if not base then return end


    local temp = readPointer(base + 0x18)
if not temp then return end
local gundyrHealth = readInteger(temp + 0xD8) or 0

    local posBase = readPointer(base + 0x68)
    if not posBase then return end
    posBase = readPointer(posBase + 0xA8)
    if not posBase then return end
    posBase = readPointer(posBase + 0x40)
    if not posBase then return end

    local gundyrX = readFloat(posBase + 0x70) or -999.0
    local gundyrY = readFloat(posBase + 0x78) or -999.0
    local gundyrZ = readFloat(posBase + 0x74) or -999.0
    local gundyrAngle = readFloat(posBase + 0x7C) or -999.0
    local animBase = readPointer(base + 0x28)
local gundyrAnim = "N/A"
if animBase then
    gundyrAnim = readString(animBase + 0x898) or "N/A"
end

    local data = string.format("%d,%.2f,%.2f,%.2f,%.2f,%s\n", gundyrHealth, gundyrX, gundyrY, gundyrZ, gundyrAngle, gundyrAnim)

    local file = io.open(file_path, "w")
    if file then
        file:write(data)
        file:close()
    end
end

myTimer = createTimer(nil, false)
myTimer.Interval = 100
myTimer.OnTimer = updateGundyrValues
myTimer.setEnabled(true)
{$asm}

[DISABLE]
{$lua}

{$asm}

