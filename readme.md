# Starlette Demo Application
## Overview

This branch contains a demo Starlette application built to showcase the functionality of the custom HTTP server implemented in the main branch.

The goal of this demo is to validate and demonstrate that the server correctly implements the ASGI specification and can successfully run real-world ASGI applications.

## Project Structure

### main branch 

- Implements a fully ASGI-compliant HTTP server from scratch.

- Handles socket management, request parsing, lifecycle events, and ASGI protocol flow.

- Designed to serve as a foundation for building custom ASGI applications and frameworks.

### This branch

- Integrates the server with a Starlette application.

- Acts as a proof-of-concept to demonstrate:

- Correct ASGI message handling

- Proper request/response lifecycle

- Compatibility with existing ASGI frameworks

## Purpose

This demo exists to:

- Verify ASGI compliance of the custom server

- Demonstrate interoperability with Starlette

- Serve as a reference example for building applications on top of the server