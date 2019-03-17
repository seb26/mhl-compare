require 'nokogiri'

doc = File.open('exampleA.mhl') { |f| Nokogiri::XML(f) }
@block = doc.xpath('//hash')

@block.each do |hash|
  puts hash.text
end
