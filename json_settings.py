import json

json_general_settings = json.dumps([
    {
        "type":"bool",
        "title":"Debug Mode",
        "desc":"Debug mode just allows the buttons and exceptions to be tested when no actual connection is present",
        "section":"General",
        "key": "dbg_mode"
    }
])

json_connection_settings = json.dumps([
    {
        "type":"string",
        "title":"IP Address",
        "desc":"IP Address",
        "section":"Connection",
        "key": "ip_addr"
    },
    {
        "type":"numeric",
        "title":"Port",
        "desc":"Port",
        "section":"Connection",
        "key": "ip_port"
    },
])

json_speed_settings = json.dumps([
    {
        "type":"numeric",
        "title":"Fan",
        "desc":"Fan Speed [%]",
        "section":"Speeds",
        "key": "fan"
    },
    {
        "type":"numeric",
        "title":"Homing",
        "desc":"Homing Speed [steps/sec]",
        "section":"Speeds",
        "key": "homing"
    },
    {
        "type":"numeric",
        "title":"Relative Move",
        "desc":'Relative Move Speed ['+u'\N{DEGREE SIGN}' + '/sec]: ',
        "section":"Speeds",
        "key": "rel_move"
    },
    {
        "type":"numeric",
        "title":"Absolute Move",
        "desc":'Absolute Move Speed ['+u'\N{DEGREE SIGN}' + '/sec]: ',
        "section":"Speeds",
        "key": "abs_move"
    },
])