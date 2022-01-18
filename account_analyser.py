import csv
import collections
import re

# Buy 28 CALEDONIA INV.@4,070 GBX (GB0001639920)
BUY_SELL_RE = '(?P<operation>Buy|Sell) (?P<n_shares>[\d,]+) (?P<product>.+)@(?P<price_per_share>[\d,.]+) (?P<currency>GBX|GBP) .*'

re_obj = re.compile(BUY_SELL_RE)

USD_GBP = 1.3513

class Product(object):

  def __init__(self):
    self.n_shares = 0
    self.current_shares_value = 0.0
    self.dividend = 0.0
    self.fees = 0.0

  def buy(self, n_shares, price_per_share):
    self.n_shares += n_shares
    self.current_shares_value -= n_shares * price_per_share

  def sell(self, n_shares, price_per_share):
    # I don't sell short
    assert(self.n_shares >= n_shares)
    self.n_shares -= n_shares
    self.current_shares_value += n_shares * price_per_share

  def add_dividend(self, amount):
    assert(amount >= 0.0)
    self.dividend += amount

  def add_fee(self, fee_amount):
    assert(fee_amount >= 0.0)
    self.fees += fee_amount

  def total_gain_loss(self):
    # the position must be closed
    assert(self.n_shares == 0)
    return self.current_shares_value + self.dividend - self.fees

  def to_string(self):
    if self.n_shares == 0:
      return f"Total gain/loss of {self.total_gain_loss():10.2f}"
    else:
      return f"Current share investment: {-self.current_shares_value:10.2f}, dividends: {self.dividend:10.2f}, fees: {self.fees:10.2f}"


if __name__ == '__main__':
  products = collections.defaultdict(Product)

  with open('C:\\Users\\SRinco\\simone\\Degiro\\Account.csv') as f:
    reader = csv.DictReader(f, delimiter=',')
    lines = [l for l in reader]

  lines.reverse()
  for line in lines:
    p = line['Product']
    d = line['Description']
    currency = line['Change']
    # Ignore some lines
    if not d:
      continue
    if d.startswith('Money Market fund conversion'):
      continue
    elif d == 'Fund Distribution':
      continue
    elif d == 'FX Credit':
      continue
    elif d == 'FX Debit':
      continue
    elif d == 'Deposit':
      continue

    is_fee = (d == 'DEGIRO Transaction and/or third party fees') or (d == 'London/Dublin Stamp Duty')
    is_dividend = (d == 'Dividend')

    assert(p)

    amount = float(line['Amount'])

    if is_fee:
      assert(currency == 'GBP')
      products[p].add_fee(-amount)
    elif is_dividend:
      if currency == 'GBP':
        products[p].add_dividend(amount)
      elif currency == 'USD':
        products[p].add_dividend(amount / USD_GBP)
      else:
        assert(false)
    else:
      # it must be a buy or sell transaction
      m = re_obj.match(d)
      assert(m)

      op = m.group('operation')
      n_shares = int(m.group('n_shares').replace(',', ''))
      price_per_share_str = m.group('price_per_share')
      price_per_share_str = price_per_share_str.replace(',', '')
      price_per_share = float(price_per_share_str)
      price_currency = m.group('currency')
      if price_currency == 'GBP':
        pass
      elif price_currency == 'GBX':
        price_per_share /= 100
      else:
        assert(false)

      if op == 'Buy':
        products[p].buy(n_shares, price_per_share)
      else:
        assert (op == 'Sell')
        products[p].sell(n_shares, price_per_share)

  gain_losses = 0.0
  fees = 0.0
  dividends = 0.0
  for p, data in products.items():
    fees += data.fees
    dividends += data.dividend
    if data.n_shares == 0:
      gain_losses += data.total_gain_loss()
    print(f'{p}: {data.to_string()}')
  print('=====')
  print(f'Total gain/loss of closed positions (includes dividends and fees): {gain_losses:10.2f}')
  print(f'Total fees: {fees:10.2f}')
  print(f'Total dividends: {dividends:10.2f}')
      

