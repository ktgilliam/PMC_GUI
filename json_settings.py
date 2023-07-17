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
        "title":"Tip/Tilt Port",
        "desc":"Port",
        "section":"Connection",
        "key": "tip_tilt_ip_port"
    },
    {
        "type":"numeric",
        "title":"TEC A Port",
        "desc":"Port",
        "section":"Connection",
        "key": "tec_a_ip_port"
    },
    {
        "type":"numeric",
        "title":"TEC B Port",
        "desc":"Port",
        "section":"Connection",
        "key": "tec_b_ip_port"
    },
])

json_motion_settings = json.dumps([
    {
        "type":"numeric",
        "title":"Fan",
        "desc":"Fan Speed [%]",
        "section":"Motion",
        "key": "fan_speed"
    },
    {
        "type":"numeric",
        "title":"Homing Speed",
        "desc":"Homing Speed [steps/sec]",
        "section":"Motion",
        "key": "homing_speed"
    },
    {
        "type":"numeric",
        "title":"Homing Timeout",
        "desc":"Homing Timeout Duration [sec]",
        "section":"Motion",
        "key": "homing_timeout"
    },
    {
        "type":"numeric",
        "title":"Relative Move",
        "desc":'Relative Move Speed ['+u'\N{DEGREE SIGN}' + '/sec]: ',
        "section":"Motion",
        "key": "rel_move"
    },
    {
        "type":"numeric",
        "title":"Absolute Move",
        "desc":'Absolute Move Speed ['+u'\N{DEGREE SIGN}' + '/sec]: ',
        "section":"Motion",
        "key": "abs_move"
    },
])