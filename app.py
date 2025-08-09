#!/usr/bin/env python3
import os

import aws_cdk as cdk

from procert_infrastructure.procert_infrastructure_stack import ProcertInfrastructureStack


app = cdk.App()
ProcertInfrastructureStack(app, "ProcertInfrastructureStack",

    )

app.synth()
