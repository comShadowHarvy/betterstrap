curl -X PATCH "https://api.cloudflare.com/client/v4/zones/4980284437a6acdcbb9a7ee42d344c3c/settings/ipv6" \
-H "X-Auth-Email: jimbob343+cloudflare@gmail.com" \
-H "X-Auth-Key: 3ee6777eebd40dbe77433d33e78c82c01ca2f" \
-H "Content-Type: application/json" \
--data '{"value":"off"}'
