# Local MCP Agent Development
Build your own agent, on your own hardware!

This is an example of setting up an agentic system using locally-hosted LLMs and MCP servers. The example here builds a dataset search tool to query the [GEO](https://www.ncbi.nlm.nih.gov/geo/) database and then save the associated metadata to a MongoDB.

## Getting Started
Main pieces required:
1. 🤖 An interface to an LLM for chatting (we use LM Studio)
1. 🛰️ A varying number of MCP servers

## 1. Installation

### LM Studio
LM Studio is a local GUI used to download and chat with various open source LLMs. 
Head to [this page](https://lmstudio.ai/download) to download LM Studio for your system. For more info, see [this page](https://lmstudio.ai/docs/app).

Once installed, download a model that can run on your hardware (i.e. you have enough memory to load the model). I've had reasonable results with `mistral-nemo-instruct-2407` on a 2025 M4 Macbook Air with 24 GB of memory.

### MCP Servers
MCP servers are web servers that expose functions as "tools" for an agent to use (as well as resources and prompts). [There's a lot more to MCP](https://modelcontextprotocol.io/docs/learn/architecture), but the idea is just a framework for designing systems in a unified way to facilitate LLM interactions. Since they're just webservers, they can be built in various ways (Javascript, Python, etc.).

An example Python-based MCP server for retrieving info from [GEO](https://www.ncbi.nlm.nih.gov/geo/) is included in this repo.

Depending on the use case, there might already be an existing implementation of an MCP server. Try searching for a desired MCP server as a starting point (e.g., [this MongoDB one](https://github.com/mongodb-js/mongodb-mcp-server) will be used later).

### Node.js
We need Javascript to run the MongoDB MCP server (which is separate from the MongoDB). To install Node and `npm`/`npx`, see [this page](https://nodejs.org/en/download).

### Docker
For this repository, we set up a MongoDB to store the metadata returned from the GEO MCP server. This requires an actual MongoDB instance running somewhere. The easiest way to do this is by spinning up a Docker image with the database, which requires installing Docker. Docker Desktop installs all the various Docker components needed.

Install Docker Desktop:
* [Mac](https://docs.docker.com/desktop/setup/install/mac-install/)
* [Windows](https://docs.docker.com/desktop/setup/install/windows-install/)
* [Linux](https://docs.docker.com/desktop/setup/install/linux/)

### Python Environment Management
Lastly, we need a way to ensure the local Python MCP server can run with the correct packages. We chose to use the environment and package manager `uv`. Detailed installation instructions can be found [here](https://docs.astral.sh/uv/getting-started/installation/), but on Mac or Linux, simply run:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## 2. Setup
Now, everything should be installed and you can start working with the actual code files.

### Clone This Repository
You need all the files locally, so clone this repository with:
```bash
git clone https://github.com/russellgould/local-mcp-dev.git
```

### Create Python Environment
Now, `cd` to the `geo-mcp-server` folder, and run:
```bash
uv sync
```

This will create the virtual environment containing the correct version of Python and all packages required for the provided MCP server.

### Start MongoDB Instance
Now, `cd` to the `mongo-db` folder and run:
```bash
docker compose up -d
```

This will start the MongoDB in the background so that the MCP server can interact with it. Note that the database contains a default username and password and thus the database will be horribly insecure. These credentials can be changed in the `mongo-db/docker-compose.yml` file. 

To kill the databsae process, run:
```bash
docker compose stop
```

If you prefer to keep this process in the foreground, just omit the `-d` option, then you can kill the process with `CTRL-C`.

### Configure MCP Servers For LM Studio
The final piece is ensuring the LM Studio knows about these MCP servers. [This page](https://lmstudio.ai/docs/app/plugins/mcp) has all the details, but you simply need a config file in your home directory. Open the following file in your preferred text editor (e.g. with `vim` or `nano`):
```bash
nano ~/.lmstudio/mcp.json
```

Then copy and paste the following into that file, ***making sure to replace <PATH_TO_THIS_REPO> with your local path***:
```json
{
  "mcpServers": {
    "MongoDB": {
      "command": "npx",
      "args": [
        "-y",
        "mongodb-mcp-server",
        "--connectionString",
        "mongodb://admin:password@localhost:27017/"
      ]
    },
    "GEO": {
      "command": "uv",
      "args": [
        "--directory",
        "<PATH_TO_THIS_REPO>/geo-mcp-server",
        "run",
        "--with",
        "fastmcp",
        "fastmcp",
        "run",
        "geo-mcp-server.py"
      ]
    }
  }
}
```

## 3. LM Studio
Now, go back to LM Studio and click the wrench icon in the top right of the window. Click the "Program" tab and you should see a list of MCP servers, with mcp/geo and mcp/mongo-db showing up in the list. You should be able to start a new chat, and select the available tools at the bottom of the chat window.

### Troubleshooting

#### If MCP Servers Have Errors In LM Studio
* Check your paths in the `~/.lmstudio/mcp.json` file.
* Ensure you started the MongoDB docker container (see instructions above)
    * Also ensure the credentials are the same in the `mcp.json` file and the Docker container

## Next Steps
Hopefully this provides a good starting point! Feel free to take this and run with it, and build on top of the MCP servers to coordinate the actual data transfer in a cleaner way and add more automation or timed updates as well.
