.. vitrage documentation master file, created by
   sphinx-quickstart on Tue Jul  9 22:26:36 2013.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Vitrage documentation!
=================================

Vitrage is the OpenStack RCA (Root Cause Analysis) service for organizing, analyzing and expanding OpenStack alarms & events, yielding insights regarding the root cause of problems and deducing their existence before they are directly detected.


High Level Functionality
------------------------

* Physical-to-Virtual entities mapping

* Deduced alarms and states (i.e., raising an alarm or modifying a state based on analysis of the system, instead of direct monitoring)

* Root Cause Analysis (RCA) for alarms/events

* Horizon plugin for the above features


Developer Guide
---------------

.. toctree::
   :maxdepth: 1

   vitrage-first_steps
   vitrage-api
   vitrage-template-format
   installation-and-configuration

Design Documents
----------------

.. toctree::
   :maxdepth: 1

   vitrage-graph-design
   scenario-evaluator
   vitrage-use-cases
   add-new-datasource

