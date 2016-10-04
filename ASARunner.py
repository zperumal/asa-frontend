#!/usr/bin/env python

""" Runs the Australian Senate Election Audit. """
import os
from aus_senate_audit.audit_recorder import AuditRecorder
from aus_senate_audit.audits.bayesian_audit import audit
from aus_senate_audit.audit_validator import AuditValidator
from aus_senate_audit.sampler.sampler_wrapper import SamplerWrapper
from aus_senate_audit.senate_election.real_senate_election import RealSenateElection

from aus_senate_audit.constants import DEFAULT_SAMPLE_INCREMENT_SIZE
from aus_senate_audit.constants import DEFAULT_SEED_VALUE
from aus_senate_audit.constants import DEFAULT_UNPOPULAR_FREQUENCY_THRESHOLD


def run(state, data, seed, sample_increment, output_name , selected_ballots=None):
    """ Runs the Australian senate election audit. """
    audit_recorder = AuditRecorder(state, audit_dir=output_name)

    if selected_ballots is None:
        #SamplerWrapper(seed, state, sample_increment, data, audit_recorder)
        done = False
        while not done:
            SamplerWrapper(seed, state, sample_increment, data, audit_recorder, quick=True)
            AuditValidator('selected_ballots.csv', audit_recorder).compare()
            election = RealSenateElection(seed, state, data, audit_recorder=audit_recorder)
            done = audit(
                election,
                seed,
                DEFAULT_UNPOPULAR_FREQUENCY_THRESHOLD,
                stage_counter=audit_recorder.get_current_audit_stage() - 1,
            )

    else:
        print("ASARUNNER... selected ballots: " + str(selected_ballots))
        print("Output name: " + str(output_name))
        print("Data: " + str(data))
        print("State " + str(state))
        AuditValidator(selected_ballots, audit_recorder).compare()
        election = RealSenateElection(seed, state, data, audit_recorder=audit_recorder)
        audit(
            election,
            seed,
            DEFAULT_UNPOPULAR_FREQUENCY_THRESHOLD,
            stage_counter=audit_recorder.get_current_audit_stage() - 1,
        )
    return audit_recorder.get_audit_info()


def run_sampler(state, data, seed, sample_increment, output_name , selected_ballots=None):
    """ Runs the Australian senate election audit. """
    audit_recorder = AuditRecorder(state, audit_dir=output_name)
    SamplerWrapper(seed, state, sample_increment, data, audit_recorder, quick=True)
    return audit_recorder.get_audit_info()
