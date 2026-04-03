import React from 'react'
import Spinner from '../media/Spinner.gif'

export default function Loader() {
  console.log("heyy")
  return (
    <div className="fixed inset-0 flex items-center justify-center bg-white/50 z-50">
      {/* Increase size here */}
      <img src={Spinner} alt="loading" className="w-32 h-32"/>
    </div>
  )
}