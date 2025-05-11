---
config:
  flowchart:
    curve: linear
---
graph TD;
	__start__([<p>__start__</p>]):::first
	agent(agent)
	tools(tools)
	__end__([<p>__end__</p>]):::last
	__start__ -. &nbsp;end&nbsp; .-> __end__;
	__start__ -.-> agent;
	__start__ -.-> tools;
	agent -. &nbsp;end&nbsp; .-> __end__;
	agent -.-> tools;
	tools -. &nbsp;end&nbsp; .-> __end__;
	tools -.-> agent;
	agent -.-> agent;
	tools -.-> tools;
	classDef default fill:#f2f0ff,line-height:1.2
	classDef first fill-opacity:0
	classDef last fill:#bfb6fc
