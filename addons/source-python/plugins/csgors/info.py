from cvars.public import PublicConVar
from plugins.info import PluginInfo


info = PluginInfo()
info.name = "CS:GO Rainbow Six Mod"
info.basename = 'csgors'
info.author = 'Kirill "iPlayer" Mysnik'
info.version = '0.1'
info.variable = '{}_version'.format(info.basename)
info.convar = PublicConVar(
    info.variable, info.version, "{} version".format(info.name))

info.url = "https://github.com/KirillMysnik/CSGO-RS"
