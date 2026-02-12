# SlowDash for Iseg

## Setup

### Native Installation

1. Install SlowDash.

    1. Clone SlowDash.
        ```bash
        git clone https://github.com/slowproj/slowdash.git --recurse-submodules
        ```

    2. Setup the environment.
        ```bash
        cd slowdash
        make
        source ./bin/slowdash-bashrc
        slowdash-activate-venv
        ```
2. Clone this repository to preferred location.
    ```
    git clone https://github.com/yano404/slowdash_iseg.git
    ```

3. Setup SlowDash for Iseg.
    1. Install `python-dotenv` inside virtual environment. 
        ```
        pip install python-dotenv
        ```
    2. Edit `.env` and `detectors.json` .

4. Start SlowDash.
    ```
    cd /path/to/slowdash_iseg
    slowdash --port=18881
    ```