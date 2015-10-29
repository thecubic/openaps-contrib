
"""
Timezones - manage timezones in diabetes data with ease.
"""

from openaps.uses.use import Use
from openaps.uses.registry import Registry

import json
import argparse
from dateutil.tz import gettz
from dateutil.parser import parse
from datetime import datetime

def set_config (args, device):
  return device

def display_device (device):
  return ''


use = Registry( )

class ConvertInput (Use):
  FIELDNAME = ['date']
  def to_ini (self, args):
    params = self.get_params(args)
    now = datetime.now( ).replace(tzinfo=args.timezone)
    params['timezone'] = now.tzname( )
    if args.date:
      params['date'] = ' '.join(args.date)
    return params
  def from_ini (self, fields):
    fields['date'] = fields['date'].split(' ')
    zone = fields.get('timezone', None)
    if zone in ['None',  None]:
      zone = gettz( )
    else:
      zone = gettz(zone)
    fields['timezone'] = zone
    fields['astimezone'] = fields.get('astimezone', False) is 'True'
    return fields
  def get_params (self, args):
    return dict(input=args.input, timezone=args.timezone, adjust=args.adjust, date=args.date, astimezone=args.astimezone)
  def configure_app (self, app, parser):
    parser.add_argument('--timezone','-z', default=gettz( ), type=gettz)
    parser.add_argument('--adjust','-a', default='missing', choices=['missing', 'replace'])
    parser.add_argument('--date','-d', action='append', default=self.FIELDNAME)
    parser.add_argument('--astimezone','-r', action='store_true',  default=False)
    parser.add_argument('input', default='-')
  def get_program (self, args):
    params = self.get_params(args)
    program = json.load(argparse.FileType('r')(params.get('input')))
    return program
  def set_converter (self, args):
    params = self.get_params(args)
    self.FIELDNAME = params.get('date')
    self.adjust = params.get('adjust')
    self.timezone = params.get('timezone')
    self.astimezone = params.get('astimezone')

  def rezone (self, dt):
    if (self.adjust == 'missing' and dt.tzinfo == None) or self.adjust == 'replace':
      dt = dt.replace(tzinfo=self.timezone) # .astimezone(self.timezone)
    if self.astimezone:
      dt = dt.astimezone(self.timezone)
    return dt
  def range (self, program):
    return [ program ]

  def convert (self, program):
    for record in self.range(program):
      fields = self.FIELDNAME
      for field in fields:
        value = record.get(field, None)
        if value is not None:
          record[field] = self.rezone(parse(value)).isoformat( )
    return program
  def main (self, args, app):
    self.set_converter(args)
    inputs = self.get_program(args)
    results = self.convert(inputs)
    return results

@use( )
class clock (ConvertInput):
  """
    Manage timezones of device clock.
  """
  FIELDNAME = None
  def get_date_value (self, record):
    return parse(record)
  def convert (self, program):
    program = self.rezone(parse(program)).isoformat( )
    return program

@use( )
class glucose (ConvertInput):
  """
    Manage timezones on glucose times.
  """
  FIELDNAME = ['dateString']
  def range (self, program):
    for record in program:
      yield record

@use( )
class rezone (glucose):
  """
    Manage how timezones are expressed in data.
  """
  FIELDNAME = ['timestamp', 'dateString', 'start_at', 'end_at', 'created_at' ]


def get_uses (device, config):
  all_uses = use.get_uses(device, config)
  all_uses.sort(key=lambda usage: getattr(usage, 'sortOrder', usage.__name__))
  return all_uses
