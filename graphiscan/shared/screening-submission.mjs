// Exact review action retained in memory after an uncertain response.
export function createReviewSubmission(makeKey) {
  let pending=null
  return {
    get pending(){return pending!==null},
    discard(){pending=null},
    async submit(client,id,body){
      if(!pending)pending={id,key:makeKey(),body:JSON.parse(JSON.stringify(body))}
      try{
        const data=await client.request('/screenings/'+encodeURIComponent(pending.id)+'/review',
          {method:'PATCH',idempotencyKey:pending.key,body:JSON.parse(JSON.stringify(pending.body))})
        pending=null;return data
      }catch(error){if(error.status===400||error.status===422)pending=null;throw error}
    }
  }
}
