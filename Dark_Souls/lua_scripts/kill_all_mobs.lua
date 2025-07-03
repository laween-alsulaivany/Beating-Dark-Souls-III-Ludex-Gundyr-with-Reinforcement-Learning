{
	Author: inuNorii
	Description: Kills all unimportant non-player entities in current area
				 Does not kill friendly NPCs, unique minibosses, or bosses
				 Feel free to report any missing enemies, ideally with IDs
}
{$lua}
if syntaxcheck then return end
[ENABLE]
local WorldChrMan = readPointer("WorldChrMan")
local SprjSessionManager = readPointer("SprjSessionManager")

local kill_list = {
	'1300', '1360', '1370', '1446', '1441', '2020', '2270', '2271', '1032', '1100', '2021',
	'1105', '1280', '1282', '1240', '1200', '1230', '1260', '3090', '2110', '2280', '1440',
	'1250', '1340', '2190', '1102', '3020', '5226', '5227', '5225', '1390', '1391', '1410',
	'3220', '1170', '1070', '1180', '2130', '2030', '1350', '5240', '2100', '3070', '2132',
	'1211', '1310', '3230', '2140', '1470', '1430', '2210', '1210', '3170', '1445', '5223',
	'1281', '1190', '6000', '6090', '6050', '6060', '6100', '6080', '6040', '6130', '6081',
	'6070', '6230', '6231', '6320', '6250', '1283', '6240', '1201', '1071', '6280', '6260',
	'6070', '6290', '6330', '6331', '3210', '2290', '1130', '3120', '2150', '3100', '1220',
	'2131', '2180', '2060', '2230', '2070', '1241', '2191', '2040', '1442', '1090', '1101',
	'1106', '3141', '1380', '2080', '6270'
}

local function kill(ptr)
	local chr_count = readInteger(ptr)
	local ChrSet = readPointer(ptr + 0x8)
	for i=1, chr_count do
		local EnemyIns = readPointer(ChrSet + i * 0x38)
		if EnemyIns ~= nil then
			local ChrModules = readPointer(EnemyIns + 0x1F90)
			if ChrModules ~= nil then
				local SprjChrDataModule = readPointer(ChrModules + 0x18)
				if SprjChrDataModule ~= nil then
					local id = readString(SprjChrDataModule + 0x132, 8, true)
					local hp = SprjChrDataModule + 0xD8
					--print(string.format("EnemyID: %s\nHP: %d\n", id, readInteger(hp)))
					if inArray(kill_list, id) then
						writeInteger(hp, 0)
					end
				end
			end
		end
	end
end

if readInteger(SprjSessionManager + 0x16C) < 4 then
	kill(readPointer(WorldChrMan + 0x1D0))
	kill(readPointer(WorldChrMan + 0x1E8))
end

disableMemrec(memrec)

[DISABLE]
