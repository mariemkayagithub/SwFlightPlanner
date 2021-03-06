  
  /** Event handler for mouse wheel event.
   */
  function wheel(event){
          var delta = 0;
          if (!event) /* For IE. */
                  event = window.event;
          if (event.wheelDelta) { /* IE/Opera. */
                  delta = event.wheelDelta/120;
                  /** In Opera 9, delta differs in sign as compared to IE.
                   */
                  if (window.opera)
                          delta = -delta;
          } else if (event.detail) { /** Mozilla case. */
                  /** In Mozilla, sign of delta is different than in IE.
                   * Also, delta is multiple of 3.
                   */
                  delta = -event.detail/3;
          }
          /** If delta is nonzero, handle it.
           * Basically, delta is now positive if wheel was scrolled up,
           * and negative, if wheel was scrolled down.
           */
          return handle_mouse_wheel(delta,event);
  }
  
  /** Initialization code. 
   * If you use your own event management code, change it as required.
   */
  if (window.addEventListener)
          /** DOMMouseScroll is for mozilla. */
          window.addEventListener('DOMMouseScroll', wheel, false);
  /** IE/Opera. */
  window.onmousewheel = document.onmousewheel = wheel; 

 
