import sys
import pytest
from commute_tube.__main__ import main, CommuteTube
from unittest.mock import patch, call
import youtube_dl

# Strategy
# 1. Write config to temp file
# 2. Start main with temp file as argument
# 3. Check if mock has been called
# 4. Check if files are in stdout

base_config_header = """{
    "pen" : {
        "penPath" : "/tmp/commuteUSB",
        "mountAndUnmount" : "False",
        "downloadFolder" : "Download",
        "common" : {
            "writesubtitles" : true,
            "format" : "bestvideo[vcodec!=?vp9]+bestaudio/best"
            }
    },
    "source" : [
    """

base_config_footer = """    ]
}"""

def init_commute_tube(tmpdir, config, additional_args, to_be_downloaded_urls):

    p = tmpdir.mkdir("commuteconfig").join("config.json")
    p.write(config)

    temp_conf_file = p.strpath

    sys.argv = [
        "commute-tube",
        "--config",
        temp_conf_file
    ]

    sys.argv.extend(additional_args)

    with pytest.raises(SystemExit) as pytest_wrapped_e:
        with patch.object(youtube_dl.YoutubeDL, 'download', return_value=None) as mock_method:
            main()
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 0

    downloaded_urls = []

    for call in mock_method.call_args_list:
        url = call[0][0][0]
        downloaded_urls.append(url)
        

    assert downloaded_urls == to_be_downloaded_urls

    mocked_parameters = []
    captured_stdout = ""

    return captured_stdout, mocked_parameters

def build_config(body):
    return base_config_header + body + base_config_footer


def test_run1(tmpdir):

    config = build_config("""
            {
            "url" : "https://www.youtube.com/user/therealgiantbomb",
            "description" : "Giant Bomb Quick Look",
            "matchtitle" : "Quick Look",
            "playlistend" : 3
        },
            {
            "url" : "test2",
            "description" : "Giant Bomb Quick Look",
            "matchtitle" : "Quick Look",
            "playlistend" : 3
        }
    """)

    init_commute_tube(
        tmpdir=tmpdir,
        config=config,
        additional_args=[],
        to_be_downloaded_urls=["https://www.youtube.com/user/therealgiantbomb", "test2"]
    )
