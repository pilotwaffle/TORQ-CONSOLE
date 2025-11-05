#!/usr/bin/env ruby
# Test Ruby Gems Functionality

require 'json'
require 'csv'
require 'date'
require 'logger'
require 'fileutils'
require 'digest'

puts "🧪 Testing Ruby Gems - #{RUBY_VERSION}"
puts "=" * 60

# Test 1: JSON gem
puts "\n📦 Test 1: JSON Gem"
data = { name: "TORQ Console", version: "0.80.0", language: "Ruby" }
json_string = JSON.generate(data)
parsed = JSON.parse(json_string)
puts "✅ JSON: Serialized and parsed successfully"
puts "   Data: #{parsed}"

# Test 2: CSV gem
puts "\n📦 Test 2: CSV Gem"
csv_string = CSV.generate do |csv|
  csv << ["Name", "Status", "Count"]
  csv << ["Ruby", "Working", 86]
  csv << ["Gems", "Installed", 42]
end
puts "✅ CSV: Generated successfully"
puts csv_string

# Test 3: Date gem
puts "\n📦 Test 3: Date Gem"
today = Date.today
puts "✅ Date: #{today} (#{today.strftime('%A, %B %d, %Y')})"

# Test 4: Logger gem
puts "\n📦 Test 4: Logger Gem"
log_file = '/tmp/ruby_test.log'
logger = Logger.new(log_file)
logger.info("Ruby gems test completed successfully")
puts "✅ Logger: Log written to #{log_file}"

# Test 5: FileUtils gem
puts "\n📦 Test 5: FileUtils Gem"
test_dir = '/tmp/ruby_test_dir'
FileUtils.mkdir_p(test_dir) unless Dir.exist?(test_dir)
puts "✅ FileUtils: Created directory #{test_dir}"

# Test 6: Digest gem
puts "\n📦 Test 6: Digest Gem"
text = "TORQ Console with Ruby"
sha256 = Digest::SHA256.hexdigest(text)
puts "✅ Digest: SHA256 hash generated"
puts "   Text: #{text}"
puts "   Hash: #{sha256[0..31]}..."

# Test 7: Minitest (just require, don't run tests)
puts "\n📦 Test 7: Minitest Gem"
require 'minitest'
puts "✅ Minitest: #{Minitest::VERSION} loaded successfully"

# Test 8: Rake (just require)
puts "\n📦 Test 8: Rake Gem"
require 'rake'
puts "✅ Rake: #{Rake::VERSION} loaded successfully"

# Summary
puts "\n" + "=" * 60
puts "🎉 All Ruby Gems Tests Passed!"
puts "=" * 60

# Return success
exit 0
