# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|
  config.vm.hostname = "soloist-test"
  config.vm.box = "devfort-ubuntu-13.04-provisionerless-120gb"
  config.vm.box_url = "http://devfort.s3.amazonaws.com/boxes/devfort-ubuntu-13.04-provisionerless-120gb-virtualbox.box"
  config.vm.network :forwarded_port, guest: 80, host: 8080
  
  script = <<SCRIPT
cd /vagrant
# Install Chef and prerequisites
apt-get -y install ruby ruby-dev git
gem install chef berkshelf
# Download the cookbooks
rm -rf Berksfile.lock
berks install --path /var/chef/cookbooks
# Run chef
chef-solo -c solo.rb -j dna.json
SCRIPT
  
  config.vm.provision "shell", inline: script
end
