# Resemble <-> React Example

This repository contains a fullstack Resemble application, inspired by Google Cloud's [Online Boutique] microservices demo.

Just like the original Online Boutique, the Resemble boutique has a frontend web
interface backed by several microservices:


| Service Name | Service Type | Description |
| --- | --- | --- |
| Cart      | Resemble | Tracks shopping cart state for each user |
| Checkout   | Resemble | Coordinates transactional orders and tracks order history |
| Currency Converter | standard gRPC | Converts between currencies, backed by a hardcoded exchange rate list |
| Emailer | Resemble using third party API | Sends emails to users via Mailgun |
| Product Catalog | Resemble | Stores details of available products |
| Shipping | Resemble | Creates and expires “shipping quotes” and “ships” orders* |

*The Resemble Boutique will not actually ship you any items.

## How to Run

## Setup in a Dev Container

[Dev Containers](https://containers.dev/) are a convenient way to create
reproducible development environments. Resemble provides a Dev Container that
has everything a Resemble application needs to run. Using that Dev Container is
normally the easiest way to start developing a Resemble application, and it can
be personalized to support your ideal workflow as your application grows.

> [!NOTE]
> The Dev Container's configuration is found in
> `.devcontainer/devcontainer.json`. You may expand on it to customize your
> development environment to your liking.

### On a GitHub Codespace

GitHub's Codespaces are Dev Containers running on cloud machines.

To try this example in a Codespace:

<!-- TODO: screenshots to support this text? -->

1. Fork this repository, so that it is owned by your own GitHub account.
2. In GitHub's webinterface, click the green "<>" (AKA "Clone, Open, or
   Download") button.
3. Select the "Codespaces" tab.
4. Click the "+" button.

This will open a cloud-hosted VSCode editor, with all of the necessary tools
installed, and with the repository's code already checked out.

### In a local Dev Container

You can also choose to run the Resemble Dev Container locally, on your own
machine. Your filesystem will be mounted into the Dev Container, so you can
develop as normal, just within the predictable environment of a Docker
container.

> [!IMPORTANT]
> Currently, the Resemble Dev Container only works on x86 CPU architectures.
> **Apple-silicon (M1/M2/...) Mac users**: we will be providing support for your
> machines soon!

Start by cloning this repository:

<!-- TODO: fetch this snippet from a test. -->

```shell
git clone https://github.com/reboot-dev/resemble-boutique.git
cd resemble-boutique/
```

How you access the Dev Container will likely depend on the editor/IDE you prefer.

#### Using VSCode

VSCode has built-in support for Dev Containers. Open your Dev Container as follows:

- In VSCode, open the `resemble-boutique` folder you've cloned.
- Press: Ctrl+Shift+P (Linux / Windows) or Command+Shift+P (Mac)
- Type/Select: `Dev Containers: Reopen In Container`

VSCode will now start your dev container, and restart VSCode to be running
inside of that container.

#### Using a non-Dev-Container-aware editor

If your editor does not have built-in support for Dev Containers, you can use
[the `devcontainer`
CLI](https://code.visualstudio.com/docs/devcontainers/devcontainer-cli).

Install the CLI as follows:

```
npm install -g @devcontainers/cli
```

Then start the Dev Container, and `exec` into it:

```
devcontainer up --workspace-folder .
devcontainer exec /bin/bash
```

## Setup without a Dev Container

> [!IMPORTANT]
> Currently, Resemble backends can only run on x86 Linux machines with
> `glibc>=2.35` (Ubuntu Jammy and other equivalent-generation Linux
> distributions). If you have a machine that doesn't fit this requirement, we
> suggest using one of the Dev Container approaches discussed above.

### Prerequisites

You must have the following tools installed:

- Python (including `pip` and `venv`) >= 3.10

### Clone Repository

Start by cloning this repository:

<!-- TODO: fetch this snippet from a test. -->

```shell
git clone https://github.com/reboot-dev/resemble-boutique.git
cd resemble-boutique/
```

### Create and activate a virtual environment

Create a new Python virtual environment in which to install Resemble
requirements and run an application:

<!-- MARKDOWN-AUTO-DOCS:START (CODE:src=./readme_test.sh&lines=32-33) -->
<!-- The below code snippet is automatically added from ./readme_test.sh -->
```sh
python -m venv ./.boutique-venv
source ./.boutique-venv/bin/activate
```
<!-- MARKDOWN-AUTO-DOCS:END -->

To learn more about why virtual environments are a best practice for Python
projects, see [the Python documentation for the `venv` module.](https://docs.python.org/3/library/venv.html)

### Install Resemble tooling

Install the Resemble command line tool (`rsm`) via `pip`. This package includes
the `rsm` CLI, the Resemble `protoc` plugin, the proto dependencies required for
Resemble definitions, and the `grpcio-tools` package that provides `protoc`.

<!-- MARKDOWN-AUTO-DOCS:START (CODE:src=./readme_test.sh&lines=39-39) -->
<!-- The below code snippet is automatically added from ./readme_test.sh -->
```sh
pip install reboot-resemble-cli
```
<!-- MARKDOWN-AUTO-DOCS:END -->

### Compile Protocol Buffers

Run the Resemble `protoc` plugin to generate Resemble code based on the protobuf
definitions for the application:

<!-- MARKDOWN-AUTO-DOCS:START (CODE:src=./readme_test.sh&lines=56-56) -->
<!-- The below code snippet is automatically added from ./readme_test.sh -->
```sh
rsm protoc
```
<!-- MARKDOWN-AUTO-DOCS:END -->

The `rsm` tool will automatically pull in required Resemble proto dependencies
like `resemble/v1alpha1/options.proto`, even though they're not found in this
repository.

<!-- TODO: link to the Resemble proto definitions once they are publicly available. -->

## Test

The example code comes with example tests. To run the example tests, use  `pytest`:

<!-- MARKDOWN-AUTO-DOCS:START (CODE:src=./readme_test.sh&lines=59-59) -->
<!-- The below code snippet is automatically added from ./readme_test.sh -->
```sh
pytest tests/
```
<!-- MARKDOWN-AUTO-DOCS:END -->

## Run

To start the application, use the `rsm` CLI:

<!--
TODO: include this command in readme_test.sh.
-->

```shell
rsm dev
```

The tool will automatically watch the application code for changes and restart the running application to reflect any updates.

<!--
TODO: introduce an `rsm grpcurl` (or `rsm call` or ...) that lets us explore
our backend in another terminal by calling RPCs.
-->
