import tiptapy


s = r"""

{
  "type": "doc",
  "content": [
    {
      "type": "code_block",
      "attrs": {
          "language": "bash"
      },
      "content": [
          {
              "type": "text",
              "text": "\n\r#!/bin/bash\n# Counting the number of lines in a list of files\n# for loop over arguments\n\nif [ $# -lt 1 ]\nthen\n  echo \"Usage: $0 file ...\"\n  exit 1\nfi\n\necho \"$0 counts the lines of code\" \nl=0\nn=0\ns=0\nfor f in $*\ndo\n\tl=`wc -l $f | sed 's/^\\([0-9]*\\).*$/\\1/'`\n\techo \"$f: $l\"\n        n=$[ $n + 1 ]\n        s=$[ $s + $l ]\ndone\n\necho \"$n files in total, with $s lines in total\" "
          }
      ]
    },
    {
      "type": "blockquote",
      "content": [
        {
          "type": "paragraph",
          "content": [
            {
              "type": "text",
              "text": "Readability counts."
            }
          ]
        },
        {
          "type": "paragraph",
          "content": [
            {
              "type": "text",
              "marks": [
                {
                  "type": "link",
                  "attrs": { "href": "https://en.wikipedia.org/wiki/Zen_of_Python" }
                }
              ],
              "text": "Zen of Python"
            },
            {
              "type": "text", "text": " By "
            },
            {
              "type": "text",
              "marks": [
                {
                  "type": "bold"
                }
              ],
              "text": "Tom Peters"
            }
          ]
        }
      ]
    }
  ]
}
"""

print(tiptapy.to_html(s))
