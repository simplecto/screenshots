# Purpose
The purpose of this project is to explore and experiment with what it takes to
make a website screen-shotting tool. At first it may seem like an easy task, 
but it becomes complex once you try. 

**NOTE**: If you just want a tool that "just works" then I suggest you try any of the
capable services linked below. 

# Common problems

  * Javascript heavy pages (almost all these days); many sites use JavaScript to
    load content after the page has downloaded into the browser. Therefore you
    need to have a modern javascript engine to parse and execute those extra
    instructions to get the content as it was intented to be seen by humans.
  * Geography-restricted content; some sites in the US have blocked visitors 
    from Europe because of GDPR. Do you accept this, or is there a way to work
    around it?
  * Bot and automation detection schemes; some sites use services to protect against
    automated processes from collecting content. This includes taking screenshots
  * Improperly configured domain names, SSL/TLS encryption certificates, and other
    network-related issues
  * Nefarious website owners and hacked sites that attempt to exploit the web browser
    to mine crypto-currencies. This puts an added load on your resources and can
    significantly slow your render-times.
  * Taking too many screenshots at a time may overload the server and cause timeouts or
    failure to load pages.
  * Temporary network or website failure; If the problem is on the site's end, then how
    will we know that and schedule another attempt later?
  * People using the service as a defacto proxy (eg- pranksters downloading porn at their
    schools or in public places)



## Requirements

Hostman to update your local /etc/hosts
`pip install pyhostman`


## Recommended reading on the subject

  * https://medium.com/@eknkc/how-to-run-headless-chrome-in-scale-7a3c7c83b28f
  * https://medium.com/@timotheejeannin/i-built-a-screenshot-api-and-some-guy-was-mining-cryptocurrencies-with-it-cd188dfae773


## Alternative Services

  * url2png.com
  * urlbox.
  * https://apiflash.com/

## Thank-yous

  * Philip Walton - (Simple sticky footers using flexbox)[https://philipwalton.github.io/solved-by-flexbox/demos/sticky-footer/] 
  * 